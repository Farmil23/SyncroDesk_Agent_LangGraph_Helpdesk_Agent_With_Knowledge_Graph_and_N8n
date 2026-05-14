import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_groq import ChatGroq


load_dotenv()

# 1. Koneksi ke database Neo4j
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
)


def _neo4j_entity_props(entity) -> dict:
    """Normalisasi properti node dari hasil driver Neo4j / LangChain."""
    if entity is None:
        return {}
    if isinstance(entity, dict):
        nested = entity.get("properties")
        if isinstance(nested, dict):
            return nested
        return entity
    return getattr(entity, "_properties", None) or {}


_USER_ASSET_CYPHER = """
MATCH (p:Person {email: $email})
OPTIONAL MATCH (p)-[:USES]->(dev:Device)
WITH p, collect(DISTINCT dev) AS devices
OPTIONAL MATCH (p)-[:BELONGS_TO]->(dept:Department)
OPTIONAL MATCH (p)-[:STATIONED_AT]->(loc:Location)
OPTIONAL MATCH (p)-[:REPORTS_TO]->(mgr:Person)
RETURN p.email AS email,
       p.name AS name,
       p.title AS title,
       p.emp_id AS emp_id,
       p.status AS status,
       devices,
       dept.name AS department,
       loc.name AS office_location,
       mgr.email AS manager_email,
       mgr.name AS manager_name
LIMIT 1
"""


def get_user_graph_context(user_email: str) -> str:
    """
    Ambil konteks Person + aset (Device lewat relasi USES) dari Neo4j untuk email request.

    Skema mengikuti sink HRIS di sync_sheet_to_graph: (:Person)-[:USES]->(:Device).
    """
    email = (user_email or "").strip()
    if not email:
        return "Neo4j query result: user email is empty; cannot query the Knowledge Graph."

    try:
        rows = graph.query(_USER_ASSET_CYPHER, {"email": email})
    except Exception as e:
        return f"Neo4j query result: failed to execute Cypher ({e})."

    if not rows:
        return (
            f"Neo4j query result: No Person node found for email '{email}'. "
            "Ensure HRIS data has been synced to the graph (/api/update-graph)."
        )

    row = rows[0]
    lines = ["Neo4j query result (Knowledge Graph), scoped to the request email:"]
    if row.get("name"):
        lines.append(f"- Name: {row['name']}")
    lines.append(f"- Email (Person): {row.get('email') or email}")
    if row.get("title"):
        lines.append(f"- Job title: {row['title']}")
    if row.get("emp_id"):
        lines.append(f"- Employee ID: {row['emp_id']}")
    if row.get("status"):
        lines.append(f"- Employment status: {row['status']}")
    if row.get("department"):
        lines.append(f"- Department: {row['department']}")
    if row.get("office_location"):
        lines.append(f"- Office location: {row['office_location']}")
    mgr_email = row.get("manager_email")
    mgr_name = row.get("manager_name")
    if mgr_email or mgr_name:
        lines.append(f"- Direct manager: {mgr_name or '-'} ({mgr_email or '-'})")

    devices = row.get("devices") or []
    asset_parts: list[str] = []
    for dev in devices:
        props = _neo4j_entity_props(dev)
        did = props.get("id")
        dtype = props.get("Device_Type")
        if did is None and dtype is None:
            continue
        label = str(did) if did is not None else "no ID"
        if dtype:
            label = f"{label} (type: {dtype})"
        asset_parts.append(label)

    if asset_parts:
        lines.append(f"- Assigned devices / assets (USES relationship): {', '.join(asset_parts)}")
    else:
        lines.append("- Devices / assets: no Device node linked in the graph for this user.")

    return "\n".join(lines)


# 2. Inisialisasi LLM Gemini untuk mengubah teks menjadi graf
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
llm_transformer = LLMGraphTransformer(llm=llm)

def extract_and_store_graph(text_data: str):
    """
    Fungsi ini akan mengubah teks biasa (misal dari data HRIS) 
    menjadi Node dan Edge di Neo4j.
    """
    documents = [Document(page_content=text_data)]
    
    print("Analyzing text and extracting graph entities...")
    
    # Proses ekstraksi oleh Gemini
    graph_documents = llm_transformer.convert_to_graph_documents(documents)
    
    # Masukkan hasil ekstraksi ke Neo4j
    graph.add_graph_documents(graph_documents)
    print("✅ Entities successfully mapped into Neo4j.")

import json
from langchain_community.graphs import Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI

# (Pastikan variabel graph sudah diinisialisasi sebelumnya)

def sync_sheet_to_graph(row_data: dict):
    print(row_data)
    email = row_data.get("Work_Email")
    if not email:
        print("❌ Error: Work_Email is missing from payload.")
        return False

    # ==========================================
    # LANGKAH 1: THE PRE-FETCH (Tarik Data Lama)
    # ==========================================
    # Kita cari relasi apa saja yang dimiliki karyawan ini sekarang
    check_query = f"""
    MATCH (p:Person {{email: '{email}'}})-[r]->(target)
    RETURN type(r) AS rel_type, labels(target)[0] AS target_label, 
           target.name AS target_name, target.id AS target_id
    """
    
    try:
        current_state_raw = graph.query(check_query)
        # Rapikan hasil agar mudah dibaca oleh LLM
        current_state = []
        for record in current_state_raw:
            target_identifier = record['target_name'] or record['target_id']
            current_state.append(
                f"- Has relationship [:{record['rel_type']}] to ({record['target_label']}: {target_identifier})"
            )

        current_state_text = (
            "\n".join(current_state)
            if current_state
            else "New employee — no relationships in the database yet."
        )
    except Exception as e:
        print(f"Error fetching current state: {e}")
        current_state_text = "Failed to load prior graph state."

    # ==========================================
    # LANGKAH 2: THE RECONCILIATION (Prompt Cerdas)
    # ==========================================

    prompt = f"""
    You are an Enterprise Neo4j reconciliation & parsing agent.
    Compare [CURRENT GRAPH STATE] with [NEW ROW DATA] and output ONE well-structured Cypher update query.

    [CURRENT GRAPH STATE]
    {current_state_text}

    [NEW ROW FROM SPREADSHEET]
    {json.dumps(row_data, indent=2)}

    Prevent "Variable `p` already declared" errors and duplicate exclusive relationships.
    You MUST follow this safe template structure:

    // 1. CREATE / UPDATE MAIN NODE
    MERGE (p:Person {{email: '{row_data.get("Work_Email")}'}})
    SET p.emp_id = '{row_data.get("Employee_ID")}',
        p.name = '{row_data.get("Full_Name")}',
        p.title = '{row_data.get("Job_Title")}',
        p.status = '{row_data.get("Employment_Status")}',
        p.years_of_service = '{row_data.get("Years_of_Service")}'
    WITH p

    // 2. REMOVE OLD EXCLUSIVE RELATIONSHIPS
    OPTIONAL MATCH (p)-[r:STATIONED_AT|BELONGS_TO|REPORTS_TO|USES]->()
    DELETE r
    WITH DISTINCT p

    // 3. CREATE TARGET NODES & NEW RELATIONSHIPS
    MERGE (d:Department {{name: '{row_data.get("Department")}'}})
    MERGE (p)-[:BELONGS_TO]->(d)

    MERGE (l:Location {{name: '{row_data.get("Office_Location")}'}})
    MERGE (p)-[:STATIONED_AT]->(l)

    MERGE (m:Person {{email: '{row_data.get("Direct_Manager_Email")}'}})
    MERGE (p)-[:REPORTS_TO]->(m)

    MERGE (dev:Device {{id: '{row_data.get("Assigned_Device_ID")}'}})
    SET dev.Device_Type = '{row_data.get("Device_Type")}'
    MERGE (p)-[:USES]->(dev)

    // 4. INCLUSIVE RELATIONSHIPS (SOFTWARE LICENSES)
    // Add Cypher to split comma-separated '{row_data.get("Software_Licenses")}', create Software nodes, and attach [:HAS_LICENSE].

    STRICT RULES:
    1. Preserve capitalization — do not lowercase payload values.
    2. Skip empty fields (null/N/A/""); do not create those nodes.
    3. Return ONLY raw Cypher text.
    """
    
    query = llm.invoke(prompt).content.strip().replace("```cypher", "").replace("```", "")
    
    # ==========================================
    # LANGKAH 3: EKSEKUSI
    # ==========================================
    try:
        graph.query(query)
        print(f"✅ State reconciliation succeeded for: {email}")
        return True
    except Exception as e:
        print(f"❌ Cypher error: {e}")
        print(f"Failed query:\n{query}")
        return False

# Contoh penggunaan saat dijalankan langsung
if __name__ == "__main__":
    # Simulasi: n8n mengirim data karyawan baru ke sistem
    mock_hr_data = "Employee Farhan works in the IT department. Farhan uses laptop asset MacBook-01. MacBook-01 is connected to the corporate backbone network."
    extract_and_store_graph(mock_hr_data)