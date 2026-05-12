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
    password=os.getenv("NEO4J_PASSWORD")
)

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
    
    print("Menganalisis teks dan mengekstrak entitas graf...")
    
    # Proses ekstraksi oleh Gemini
    graph_documents = llm_transformer.convert_to_graph_documents(documents)
    
    # Masukkan hasil ekstraksi ke Neo4j
    graph.add_graph_documents(graph_documents)
    print("✅ Entitas berhasil dipetakan ke dalam Neo4j.")

# Contoh penggunaan saat dijalankan langsung
if __name__ == "__main__":
    # Simulasi: n8n mengirim data karyawan baru ke sistem
    mock_hr_data = "Karyawan bernama Farhan bekerja di departemen IT. Farhan menggunakan laptop seri MacBook-01. MacBook-01 terhubung ke Jaringan Utama."
    extract_and_store_graph(mock_hr_data)