from langchain_google_genai import ChatGoogleGenerativeAI
from database.vector_db import get_retriever
from database.graph_db import get_user_graph_context
from agents.state import AgentState
from langchain_groq import ChatGroq
from agents.prompts import TRIAGE_PROMPT, DRAFTER_PROMPT, GUARDRAIL_PROMPT
# Konstanta & vector store cache (satu instance sepanjang hidup proses Python)
from cag.cache import CACHE_THRESHOLD, QA_CACHE, build_cache_query_text, cache_aktif

import json
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


def triage_node(state: AgentState):
    """Agen 1: Menentukan kategori masalah (IT / HR / FINANCE / GENERAL)."""
    prompt = TRIAGE_PROMPT.format(issue_text=state["issue_text"])
    response = llm.invoke(prompt)
    return {"category": response.content}


def normalize_query_node(state: AgentState):
    """
    Agen "normalize" (persiapan cache).

    Setelah triage, kita sudah punya `category`. Di sini kita gabungkan:
      issue_text + user_email + category
    jadi satu string `normalized_issue` yang konsisten untuk di-embed ke FAISS.

    Node berikutnya (cache_lookup) akan pakai string ini untuk similarity search.
    """
    query = build_cache_query_text(
        state["issue_text"],
        state["user_email"],
        state.get("category", ""),
    )
    return {"normalized_issue": query}


def semantic_cache_lookup_node(state: AgentState):
    """
    Agen "cache lookup": tanya ke QA_CACHE, apakah pernah ada tiket mirip?

    Langkah:
      1. Kalau fitur cache dimatikan di .env → anggap selalu MISS (supaya tetap query DB).
      2. Kalau index FAISS masih kosong (ntotal == 0) → MISS.
      3. Cari 1 dokumen terdekat (k=1) + jarak L2-nya (score).
      4. Kalau score <= CACHE_THRESHOLD → HIT: isi retrieved_docs & user_context dari metadata.
      5. Kalau tidak → MISS: nanti investigator yang mengisi field itu.
    """
    # Fitur cache nonaktif → selalu lewat jalur investigator
    if not cache_aktif():
        print("--- CACHE OFF ---")
        return {"cache_hit": False}

    query = state.get("normalized_issue", "")

    # Belum pernah ada yang disimpan ke QA_CACHE
    if QA_CACHE.index.ntotal == 0:
        print("--- CACHE MISS (empty index) ---")
        return {"cache_hit": False}

    # hits[0] = (dokumen_langchain, jarak_L2)
    hits = QA_CACHE.similarity_search_with_score(query, k=1)
    doc, score = hits[0]

    # Semakin kecil score → semakin mirip vektor query dengan yang tersimpan
    if score <= CACHE_THRESHOLD:
        print(f"--- CACHE HIT (L2 distance: {score:.4f}) ---")
        meta = doc.metadata or {}
        return {
            "cache_hit": True,
            "retrieved_docs": str(meta.get("retrieved_docs", "")),
            "user_context": str(meta.get("user_context", "")),
        }

    print("--- CACHE MISS ---")
    return {"cache_hit": False}


def cache_write_node(state: AgentState):
    """
    Agen "cache write": simpan hasil investigator ke QA_CACHE untuk pemakaian berikutnya.

    Hanya jalan kalau:
      - cache_aktif() True, DAN
      - tiket ini tadi MISS (bukan HIT), DAN
      - ada string normalized_issue.

    Pakai add_texts:
      - texts[0]        = string yang sama dengan yang dipakai saat lookup (normalized_issue)
      - metadatas[0]    = dict berisi retrieved_docs & user_context hasil DB

    Kalau sudah HIT dari lookup, tidak usah menulis lagi (data sudah ada di index dari tiket lalu).
    """
    if not cache_aktif():
        return {}

    # Kalau tadi dapat jawaban dari cache, jangan dobel simpan
    if state.get("cache_hit"):
        return {}

    question = state.get("normalized_issue", "")
    if not question:
        return {}

    rd = state.get("retrieved_docs", "")
    uc = state.get("user_context", "")

    QA_CACHE.add_texts(
        texts=[question],
        metadatas=[{"retrieved_docs": rd, "user_context": uc}],
    )
    print("--- CONTEXT CACHED (add_texts) ---")
    return {}


def retriever_node(state: AgentState):
    """
    Agen 2 (investigator): ambil konteks dari Chroma + Neo4j (Cypher ke Knowledge Graph).

    Node ini HANYA dipanggil pada jalur MISS cache (lihat graph.py).
    Hasilnya akan ditulis ke QA_CACHE oleh cache_write_node.
    """
    retriever = get_retriever()
    docs = retriever.invoke(state["issue_text"])
    context_text = "\n".join([d.page_content for d in docs])

    user_info = get_user_graph_context(state["user_email"])

    return {"retrieved_docs": context_text, "user_context": user_info}


def drafter_node(state: AgentState):
    """Agen 3: Tulis draf email pakai category + retrieved_docs + user_context (dari DB atau cache)."""
    prompt = DRAFTER_PROMPT.format(
        category=state.get("category", "GENERAL"),
        retrieved_docs=state.get("retrieved_docs", ""),
        user_context=state.get("user_context", ""),
        issue_text=state["issue_text"],
    )

    response = llm.invoke(prompt)
    return {"draft_response": response.content}


# def guardrail_node(state: AgentState):
#     """Agen 4: Cek apakah draf aman untuk dikirim."""
#     prompt = GUARDRAIL_PROMPT.format(draft_response=state["draft_response"])

#     response = llm.invoke(prompt)
#     safe = "YA" in response.content.upper()
#     return {"is_safe": safe}


def guardrail_node(state: AgentState):
    prompt = GUARDRAIL_PROMPT.format(draft_response=state['draft_response'])
    response = llm.invoke(prompt)
    
    try:
        # Parsing JSON dari Gemini
        eval_result = json.loads(response.content.strip())
        aman = eval_result.get("is_safe", False)
        alasan = eval_result.get("reason", "Potential policy violation detected.")
    except Exception as e:
        # Fallback jika Gemini gagal output JSON
        aman = False
        alasan = "Failed to validate draft safety."

    if not aman:
        print(f"🚨 GUARDRAIL TRIGGERED: {alasan}")
        # OVERRIDE: Timpa jawaban Drafter dengan pesan eskalasi
        pesan_eskalasi = (
            f"⚠️ [SECURITY SYSTEM ACTIVE]\n"
            f"Your request could not be processed automatically by our AI agent because: {alasan}.\n"
            f"Your ticket has been locked and escalated to the relevant manager for manual review."
        )
        return {"is_safe": False, "draft_response": pesan_eskalasi}
        
    return {"is_safe": True}