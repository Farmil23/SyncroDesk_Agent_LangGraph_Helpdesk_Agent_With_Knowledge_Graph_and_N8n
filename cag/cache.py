"""
Modul ini menyiapkan "vector cache" pakai FAISS — pola seperti di notebook.

Apa yang di-cache di sini?
  Bukan jawaban LLM, tapi hasil retrieval: teks SOP (retrieved_docs) + konteks user (user_context).
  Kalau tiket baru mirip dengan yang pernah diproses, kita bisa pakai ulang teks itu
  dan melewati query ke Chroma/Neo4j (lebih cepat).

Bagaimana cara kerjanya (intuisi)?
  1. Kita ubah deskripsi tiket jadi satu string panjang (lihat build_cache_query_text).
  2. String itu di-embed jadi vektor angka, disimpan di index FAISS.
  3. Tiket baru: embed string yang sama → cari tetangga terdekat di index.
  4. Kalau "jarak" L2 ke tetangga terdekat <= CACHE_THRESHOLD → dianggap mirip → pakai metadata-nya.
"""

import os

import faiss
from dotenv import load_dotenv
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# ----- QA CACHE (EMPTY, SAFE INIT) -----
# IndexFlatL2 = ukur "jarak" antar vektor (semakin kecil = semakin mirip).
# Docstore kosong {} = belum ada dokumen; aman di awal aplikasi.
# embedding_function = model yang dipakai untuk ubah teks → vektor (harus sama dimensi dengan dim).
dim = 1536  # ukuran vektor untuk model text-embedding-3-small (OpenAI)
qa_index = faiss.IndexFlatL2(dim)
QA_CACHE = FAISS(
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    index=qa_index,
    docstore=InMemoryDocstore({}),
    index_to_docstore_id={},
)

# Batas "mirip": score dari similarity_search_with_score = jarak L2.
# Semakin KECIL angka ini → semakin KETAT (harus sangat mirip baru dianggap cache HIT).
CACHE_THRESHOLD = float(os.getenv("CACHE_THRESHOLD", "0.4"))


def cache_aktif() -> bool:
    """
    Cache hanya dipakai kalau kamu sengaja menyalakannya di .env.

    Kenapa default mati?
      Supaya perilaku API tetap sama seperti sebelum ada cache,
      sampai kamu set CAG_ENABLED=true di environment.
    """
    v = os.getenv("CAG_ENABLED", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def build_cache_query_text(issue_text: str, user_email: str, category: str) -> str:
    """
    Bangun SATU string yang akan di-embed dan dipakai untuk cari di QA_CACHE.

    Kenapa gabung issue + email + kategori?
      - Issue: inti pertanyaan user (mirip antar tiket).
      - Email: konteks aset/user bisa beda per orang.
      - Kategori: hasil triage (IT/HR/...) supaya cache IT tidak tertukar dengan HR.
    """
    q = issue_text.strip().lower()
    email = user_email.strip().lower()
    cat = (category or "").strip().upper()
    return f"{q} | {email} | {cat}"
