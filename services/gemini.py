import logging
from typing import List

from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah asisten AI WhatsApp yang ramah, sopan, dan memberikan jawaban singkat serta jelas.
- Jawab pertanyaan dengan bahasa Indonesia yang santai namun tetap menghormati pengguna.
- Hindari jawaban yang terlalu panjang; maksimal 2-3 kalimat.
- Jika tidak tahu jawabannya, katakan dengan jujur dan tawarkan bantuan lain.
- Selalu akhiri dengan salam atau ungkapan positif.
"""


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.system_instruction = getattr(
            settings,
            "gemini_system_instruction",
            SYSTEM_PROMPT,
        )

        # Ambil model utama dari .env
        raw_primary = getattr(settings, "gemini_model", "gemini-1.5-flash")
        
        # Ambil fallback models dari .env
        raw_fallback = getattr(
            settings,
            "mini_fallback_models",
            "gemini-1.5-pro,gemini-2.0-flash",
        )

        # Gabungkan dan format nama model
        candidates = [raw_primary] + [m.strip() for m in raw_fallback.split(",") if m.strip()]
        
        self._fallback_models = []
        for model in candidates:
            # Pastikan format bersih tanpa duplikasi 'models/'
            clean_name = model.replace("models/", "")
            full_model_name = f"models/{clean_name}"
            
            if full_model_name not in self._fallback_models:
                self._fallback_models.append(full_model_name)

        logger.info(f"Loaded Gemini models: {self._fallback_models}")
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.system_instruction = getattr(
            settings,
            "gemini_system_instruction",
            SYSTEM_PROMPT,
        )

        # Parse model dari .env dan pastikan menggunakan awalan 'models/'
        primary_model = getattr(settings, "gemini_model", "models/gemini-2.0-flash")
        if not primary_model.startswith("models/"):
            primary_model = f"models/{primary_model}"

        fallback_raw = getattr(
            settings,
            "mini_fallback_models",
            "models/gemini-1.5-flash,models/gemini-1.5-pro",
        )
        
        fallback_list = []
        for m in fallback_raw.split(","):
            m = m.strip()
            if m:
                if not m.startswith("models/"):
                    m = f"models/{m}"
                fallback_list.append(m)

        self._fallback_models = [primary_model] + [
            m for m in fallback_list if m != primary_model
        ]

    def _build_prompt(self, user_message: str, chat_history: List[dict]) -> str:
        context = ""
        if chat_history:
            context = "Riwayat percakapan sebelumnya:\n"
            for msg in chat_history[-5:]:
                role = "Pengguna" if msg["role"] == "user" else "Asisten"
                context += f"{role}: {msg['message']}\n"
            context += "\n"
        return f"{self.system_instruction}\n\n{context}Pengguna: {user_message}\n\nAsisten:"

    async def generate_response_with_history(self, user_message: str, chat_history: List[dict]) -> str:
        prompt = self._build_prompt(user_message, chat_history)

        for model_name in self._fallback_models:
            try:
                logger.info(f"Mencoba model Gemini: {model_name}")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=500,
                    ),
                )
                if response and response.text:
                    logger.info(
                        f"Response berhasil dari model {model_name} untuk pesan: {user_message[:30]}"
                    )
                    return response.text.strip()
            except Exception as exc:
                logger.error(
                    f"Error saat menggunakan model Gemini {model_name}: {exc}"
                )
                continue

        fallback_msg = (
            "Maaf, saya sedang mengalami kendala teknis. "
            "Silakan coba lagi nanti atau hubungi tim support."
        )
        logger.error("Semua model Gemini gagal. Mengembalikan fallback message.")
        return fallback_msg

    async def generate_response(self, user_message: str, chat_history: List[dict] | None = None) -> str:
        if chat_history is None:
            chat_history = []
        return await self.generate_response_with_history(user_message, chat_history)


gemini_service = GeminiService()