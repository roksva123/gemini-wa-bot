import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# Konfigurasi Provider (Diambil langsung dari hasil tes model aktif)
PROVIDERS = {
    "groq": {
        "model": "openai/gpt-oss-20b",
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1"
    },
    "nvidia": {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "api_key_env": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1"
    }
}

async def generate_ai_response(
    prompt: str, 
    system_instruction: str = "Kamu adalah asisten WhatsApp yang ramah dan solutif."
) -> str:
    """
    Mencoba memanggil provider AI secara berurutan (Groq -> NVIDIA -> OpenAI).
    Jika provider utama gagal, otomatis melempar ke provider cadangan.
    """
    provider_order = ["groq", "nvidia", "openai"]

    for provider_name in provider_order:
        config = PROVIDERS.get(provider_name)
        if not config:
            continue

        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            logger.warning(f"API key untuk {provider_name} ({config['api_key_env']}) tidak ditemukan di .env")
            continue

        try:
            logger.info(f"Mencoba menghasilkan respon menggunakan provider: {provider_name} ({config['model']})")

            client = OpenAI(
                api_key=api_key,
                base_url=config.get("base_url")
            )

            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content
            if result_text:
                logger.info(f"Respon berhasil didapat dari {provider_name}")
                return result_text.strip()

        except Exception as e:
            logger.warning(
                f"Provider {provider_name} gagal dengan error: {str(e)}. "
                f"Mengalihkan ke provider berikutnya..."
            )
            continue

    return "Maaf, seluruh layanan AI sedang mengalami kendala. Silakan coba beberapa saat lagi."