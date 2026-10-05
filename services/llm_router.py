"""
LLM Router dengan fallback antar provider (Groq -> NVIDIA -> OpenAI)
Mendukung format messages array untuk multi-turn conversations
"""
import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# Konfigurasi Provider dengan API keys dari env
PROVIDERS = {
    "groq": {
        "model": "mixtral-8x7b-32768",
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1"
    },
    "nvidia": {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "api_key_env": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1"
    },
    "openai": {
        "model": "gpt-3.5-turbo",
        "api_key_env": "OPENAI_API_KEY",
        "base_url": None  # OpenAI menggunakan default base URL
    }
}


async def generate_ai_response(
    messages: List[Dict[str, str]],
    system_instruction: str = "Kamu adalah asisten WhatsApp yang ramah dan solutif.",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    timeout: float = 30.0
) -> str:
    """
    Generate respons AI dengan fallback antar provider

    Args:
        messages: List of messages dalam format [{"role": "user", "content": "..."}, ...]
        system_instruction: System prompt/instruction untuk LLM
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum tokens untuk respons
        timeout: Timeout untuk API call dalam detik

    Returns:
        String respons dari LLM

    Raises:
        Exception jika semua provider gagal
    """

    provider_order = ["groq", "nvidia", "openai"]
    last_error = None

    for provider_name in provider_order:
        config = PROVIDERS.get(provider_name)
        if not config:
            logger.warning(f"Provider {provider_name} tidak ditemukan di konfigurasi")
            continue

        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            logger.warning(
                f"API key untuk {provider_name} ({config['api_key_env']}) tidak ditemukan di .env"
            )
            continue

        try:
            logger.info(
                f"Mencoba generate respons menggunakan provider: {provider_name} "
                f"(model: {config['model']})"
            )

            # Siapkan messages dengan system instruction
            full_messages = [
                {"role": "system", "content": system_instruction}
            ] + messages

            # Create client dengan base_url yang sesuai
            client_kwargs = {
                "api_key": api_key,
            }
            if config.get("base_url"):
                client_kwargs["base_url"] = config["base_url"]

            client = OpenAI(**client_kwargs)

            # Call LLM
            response = client.chat.completions.create(
                model=config["model"],
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )

            # Extract respons
            result_text = response.choices[0].message.content
            if result_text:
                logger.info(f"Respons berhasil didapat dari {provider_name}")
                return result_text.strip()

        except Exception as e:
            error_msg = str(e)
            logger.warning(
                f"Provider {provider_name} gagal dengan error: {error_msg}. "
                f"Mengalihkan ke provider berikutnya..."
            )
            last_error = e
            continue

    # Semua provider gagal
    error_summary = str(last_error) if last_error else "Unknown error"
    logger.error(f"Semua provider gagal. Error terakhir: {error_summary}")

    return "Maaf, seluruh layanan AI sedang mengalami kendala. Silakan coba beberapa saat lagi."


async def generate_ai_response_legacy(
    prompt: str,
    system_instruction: str = "Kamu adalah asisten WhatsApp yang ramah dan solutif."
) -> str:
    """
    Legacy function untuk backward compatibility
    Konversi prompt string ke format messages array dan panggil generate_ai_response
    """
    messages = [{"role": "user", "content": prompt}]
    return await generate_ai_response(
        messages=messages,
        system_instruction=system_instruction
    )
