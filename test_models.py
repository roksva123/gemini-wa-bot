import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_groq():
    print("\n--- TESTING GROQ ---")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[GROQ] GROQ_API_KEY tidak ditemukan di .env")
        return

    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    
    # Cek daftar model yang tersedia untuk API Key ini
    try:
        models = client.models.list()
        print("[GROQ] Model aktif yang tersedia untuk akun Anda:")
        for m in models.data:
            print(f"  - {m.id}")
    except Exception as e:
        print(f"[GROQ] Gagal mengambil daftar model: {e}")

def test_nvidia():
    print("\n--- TESTING NVIDIA NIM ---")
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("[NVIDIA] NVIDIA_API_KEY tidak ditemukan di .env")
        return

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    
    # Cek daftar model NVIDIA
    try:
        models = client.models.list()
        print("[NVIDIA] Model aktif yang tersedia untuk akun Anda:")
        for m in models.data:
            print(f"  - {m.id}")
    except Exception as e:
        print(f"[NVIDIA] Gagal mengambil daftar model: {e}")

if __name__ == "__main__":
    test_groq()
    test_nvidia()