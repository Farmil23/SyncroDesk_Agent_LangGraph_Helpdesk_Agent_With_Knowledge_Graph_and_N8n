import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.graph import app_graph  # Import graf yang sudah di-compile
from agents.observability import (
    build_demo_observability,
    emit_structured_ticket_log,
    observability_demo_enabled,
    observability_or_logging_enabled,
)
from database.graph_db import sync_sheet_to_graph
from database.sqlite_db import init_db, insert_ticket, get_all_tickets, get_ticket_by_id


app = FastAPI(title="SyncroDesk AI Engine")

@app.on_event("startup")
def startup_event():
    init_db()

class TicketRequest(BaseModel):
    ticket_id: str = None
    user_email: str
    issue_text: str

@app.post("/api/ticket")
async def process_ticket(ticket: TicketRequest):
    if not ticket.ticket_id:
        ticket.ticket_id = str(uuid.uuid4())
        
    try:
        # 1. State awal untuk LangGraph (semua key yang dipakai AgentState harus ada nilai awal)
        initial_state = {
            "ticket_id": ticket.ticket_id,
            "user_email": ticket.user_email,
            "issue_text": ticket.issue_text,
            "messages": [],
            # Diisi node "triage" (klasifikasi departemen)
            "category": "",
            # Diisi node "cache_lookup" (HIT) atau "investigator" (MISS)
            "retrieved_docs": "",
            "user_context": "",
            # Diisi node "drafter" / "guardrail"
            "draft_response": "",
            "is_safe": True,
            # --- cache FAISS: nilai awal sebelum node normalize / cache_lookup ---
            "cache_hit": False,       # True hanya kalau konteks dari QA_CACHE
            "normalized_issue": "",  # Diisi node "normalize" (string untuk embed)
        }

        # 2. Jalankan LangGraph
        # Alur: triage → normalize → cache_lookup → (hit: drafter | miss: investigator → cache_write → drafter) → guardrail
        t0 = time.perf_counter()
        result = app_graph.invoke(initial_state)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # 3. Observability processing
        obs = None
        cache_hit_status = False
        if observability_or_logging_enabled() or True: # Always collect observability for dashboard
            obs = build_demo_observability(result, elapsed_ms)
            cache_hit_status = obs.get("cache", {}).get("hit", False)
            emit_structured_ticket_log(result["ticket_id"], obs)

        # 4. Simpan ke SQLite
        db_ticket_data = {
            "ticket_id": result["ticket_id"],
            "user_email": ticket.user_email,
            "issue_text": ticket.issue_text,
            "category": result["category"],
            "status": "Requires Review",
            "resolution": result["draft_response"],
            "investigation_log": {
                "sop_found": True if result["retrieved_docs"] else False,
                "asset_context": result["user_context"],
                "tracing": {
                    "duration": f"{round(elapsed_ms/1000, 2)}s",
                    "path": "Cache Hit" if cache_hit_status else "Cache Miss -> Investigator -> Drafter -> Guardrail"
                }
            },
            "cache_hit": cache_hit_status
        }
        insert_ticket(db_ticket_data)

        # 5. Kirim hasil final kembali ke frontend/n8n
        body = {
            "status": "success",
            "ticket_id": result["ticket_id"],
            "category": result["category"],
            "resolution": result["draft_response"],
            "investigation_log": db_ticket_data["investigation_log"],
            "cache_status": "Hit" if cache_hit_status else "Miss"
        }
        
        if obs and observability_demo_enabled():
            body["observability"] = obs

        return body

    except Exception as e:
        print(f"[CRITICAL ERROR AI PROCESSING] -> {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickets")
async def get_tickets():
    tickets = get_all_tickets()
    return {"status": "success", "data": tickets}

@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "success", "data": ticket}

@app.post("/api/update-graph")
async def update_graph(data: dict):
    # 'data' adalah satu baris dari Google Sheets yang dikirim n8n
    success = sync_sheet_to_graph(data)
    if success:
        return {"status": "synced", "data": data}
    else:
        return {"status": "error", "message": "Failed to update graph"}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        proxy_headers=True, 
        forwarded_allow_ips="*"
    )