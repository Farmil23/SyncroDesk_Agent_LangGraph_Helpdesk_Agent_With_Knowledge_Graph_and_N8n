
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# Konfigurasi Direktori
SOP_FOLDER = "./data/sops" 
CHROMA_DB_DIR = "./chroma_db"
PATH = []

# Inisialisasi Model Embedding Gemini
# embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
)

def ingest_documents():
    """Fungsi Pipeline: Load, Split, dan Store dokumen SOP ke Vector DB"""
    
    # Pastikan folder ada
    if not os.path.exists(SOP_FOLDER):
        os.makedirs(SOP_FOLDER)
        print(f"Created folder {SOP_FOLDER}. Add your SOP PDF files there.")
        return

    print(f"Loading documents from {SOP_FOLDER}...")
    
    # 1. LOAD: Reading the file pdf dokumen in SOP folder
    loader = DirectoryLoader(
        './data/sops', 
        glob="**/*.pdf", 
        loader_cls=PyPDFLoader
    )
    
    documents = loader.load()
    
    for i, path in enumerate(documents):
        path_docs = documents[i].metadata['source']
        PATH.append(path_docs)
        
    print(PATH)
        
    if not documents:
        print("❌ No .pdf documents found under data/sops/")
        return

    print(f"✅ Loaded {len(documents)} document(s).")

    # 2. SPLIT: Memecah dokumen menjadi potongan kecil (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # Maksimal karakter per potongan
        chunk_overlap=50,     # Irisan antar potongan agar konteks kalimat tidak terpotong
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Split into {len(chunks)} chunk(s).")

    # 3. STORE: Mengubah chunk teks menjadi vektor (Embed) dan menyimpannya di ChromaDB
    print("Embedding and persisting to ChromaDB...")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings_model,
        persist_directory=CHROMA_DB_DIR
    )
    print("✅ RAG ingest complete. Documents are ready for the LangGraph agent.")

def get_retriever():
    """Fungsi untuk dipanggil oleh LangGraph nanti saat mencari jawaban"""
    vector_db = Chroma(
        persist_directory=CHROMA_DB_DIR, 
        embedding_function=embeddings_model
    )
    # Mengembalikan objek retriever yang mencari 2 dokumen paling relevan
    return vector_db.as_retriever(search_kwargs={"k": 2})

# Eksekusi pipeline saat file ini dijalankan langsung di terminal
if __name__ == "__main__":
    ingest_documents()