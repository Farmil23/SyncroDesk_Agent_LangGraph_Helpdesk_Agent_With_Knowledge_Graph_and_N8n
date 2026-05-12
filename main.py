import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.graph import app_graph  # Import graf yang sudah di-compile

app = FastAPI(title="SyncroDesk AI Engine")

class TicketRequest(BaseModel):
    ticket_id: str = str(uuid.uuid4())
    user_email: str
    issue_text: str

@app.post("/api/ticket")
async def process_ticket(ticket: TicketRequest):
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
        result = app_graph.invoke(initial_state)

        # 3. Kirim hasil final kembali ke n8n
        return {
            "status": "success",
            "ticket_id": result["ticket_id"],
            "category": result["category"],
            "resolution": result["draft_response"],
            "investigation_log": {
                "sop_found": True if result["retrieved_docs"] else False,
                "asset_context": result["user_context"]
            }
        }

    except Exception as e:
        print(f"[CRITICAL ERROR AI PROCESSING] -> {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        proxy_headers=True, 
        forwarded_allow_ips="*"
    )