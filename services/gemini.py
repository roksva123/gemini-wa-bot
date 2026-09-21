import logging
from typing import List

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service untuk integrasi dengan Google Gemini API"""

    def __init__(self):
        """Inisialisasi Gemini client satu kali"""
        # Configure API key once
        genai.configure(api_key=settings.gemini_api_key)
        # Store model name
        self.model_name = settings.gemini_model
        # System instruction can be overridden via env if needed
        self.system_instruction = getattr(settings, "gemini_system_instruction", """Kamu adalah Asisten Virtual yang ramah, pintar, dan responsif.
Berikut adalah karakteristikmu:
- Jawab pertanyaan dengan jelas, ringkas, dan terstruktur
- Gunakan poin-poin (bullet points) untuk informasi yang kompleks
- Gunakan **teks tebal** untuk hal-hal penting
- Hindari jawaban yang terlalu panjang (maksimal 2-3 paragraf atau 5 poin)
- Jika pertanyaan tidak jelas, tanyakan pertanyaan klarifikasi
- Selalu ramah dan membantu
- Jika tidak tahu jawaban, katakan dengan jujur daripada mengada-ada""")
        # Prepare a reusable GenerativeModel with a fixed GenerationConfig
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=500,
        )
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
        )

    def format_chat_history(self, chat_history: List[dict]) -> List[dict]:
        """Format riwayat chat untuk Gemini API"""
        formatted_history = []
        for msg in chat_history:
            formatted_history.append(
                {
                    "role": msg["role"],
                    "parts": [{"text": msg["message"]}],
                }
            )
        return formatted_history

    def _generate_content(self, contents: str):
        """Generate content menggunakan SDK google-generativeai dengan model yang sudah di‑initialize."""
        prompt = f"{self.system_instruction}\n\n{contents}"
        return self.model.generate_content(prompt)

    async def generate_response(self, user_message: str, chat_history: List[dict]) -> str:
        """Generate respons menggunakan Gemini dengan chat history"""
        try:
            response = self._generate_content(user_message)

            # Extract text dari response
            if response.text:
                logger.info(
                    f"Gemini response generated successfully for message: {user_message[:50]}"
                )
                return response.text

            logger.warning("Empty response from Gemini API")
            return "Maaf, saya tidak dapat menghasilkan respons saat ini. Silakan coba lagi."

        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            return f"Terjadi kesalahan saat memproses pertanyaan Anda: {str(e)}"

    async def generate_response_with_history(self, user_message: str, chat_history: List[dict]) -> str:
        """Generate respons dengan memasukkan chat history untuk konteks yang lebih baik"""
        try:
            # Format history untuk digunakan sebagai konteks
            context = ""
            if chat_history:
                context = "Riwayat percakapan sebelumnya:\n"
                for msg in chat_history[-5:]:  # Ambil 5 pesan terakhir
                    role = "Pengguna" if msg["role"] == "user" else "Asisten"
                    context += f"{role}: {msg['message']}\n"
                context += "\n"

            # Gabungkan konteks dengan pesan baru
            full_message = context + f"Pengguna: {user_message}\n\nAsisten:"

            # Generate response
            response = self._generate_content(full_message)

            if response.text:
                logger.info("Gemini response with history generated successfully")
                return response.text.strip()

            return "Maaf, saya tidak dapat menghasilkan respons saat ini."

        except Exception as e:
            logger.error(f"Error in generate_response_with_history: {str(e)}")
            return "Terjadi kesalahan saat memproses permintaan Anda."


# Inisialisasi singleton instance
gemini_service = GeminiService()
