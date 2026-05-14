import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key = api_key,
    temperature=0.7
)

# 3. Tes Koneksi dengan invoke sederhana
try:
    response = llm.invoke("Halo Gemini, apakah koneksi kita sudah berhasil?")
    print("--- Respon dari Gemini ---")
    print(response.content)
    print("\n[Status]: Koneksi Berhasil! ✅")
except Exception as e:
    print(f"\n[Status]: Koneksi Gagal! ❌\nError: {e}")