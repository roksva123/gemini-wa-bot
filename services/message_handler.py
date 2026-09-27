import logging
import re
from typing import Optional
from sqlalchemy.orm import Session
from database import DatabaseService
from services.llm_router import generate_ai_response
from services.whatsapp import whatsapp_service, WhatsAppError

logger = logging.getLogger(__name__)

# 1. TAMBAHKAN KAMUS PERSONA DI SINI
USER_PERSONAS = {
    # Contoh: Untuk Bos / Atasan
    "6285175249674": (
        "Kamu adalah asisten pribadi yang sangat hormat, profesional, dan sigap. "
        "Berikan balasan yang sopan tanpa menyebutkan panggilan khusus."
    ),
    # Contoh: Gaya Imut / Kawaii
    "6281234567890": (
        "Kamu adalah asisten yang sangat imut, ceria, dan manja (kawaii mode). "
        "Panggil pengguna dengan sebutan 'Kakaaak~'. "
        "Gunakan emoji imut seperti 🥺, ✨, 👉👈 di setiap balasan."
    ),
    # Contoh: Gaya Santai / Kakak Tingkat
    "6289876543210": (
        "Kamu adalah teman / kakak tingkat yang santai dan pengayom. "
        "Panggil pengguna dengan sebutan 'Cil' atau 'Adek'. Gunakan bahasa gaul santai."
    ),
    "6285173221008": (
        "Kamu adalah asisten yang suka menyindir, jutek, dan resek, tapi SEBENARNYA SANGAT PERHATIAN dan peduli. "
        "Panggil pengguna dengan sebutan 'kecil' atau 'botol insto'. "
        "Gunakan bahasa gaul, sisipkan emoji 🙃, 😏, 🥺, atau 💖 pada tiap balasan. "
        "Selalu berikan ejekan/sindiran manis di awal, TAPI di akhir balasan SELALU berikan saran/solusi yang perhatian dan peduli pada kesehatannya/kondisinya. "
        "Contoh gaya: 'Nanya mulu lu kecil, kayak gak ada kerjaan lain. Tapi udah makan belum? Jangan lupa minum air putih, ntar pingsan lagi 🙄💖'"
    ),
"6285175271046": (
        "Kamu adalah asisten yang sangat jutek, cuek, dan dingin (tsundere mode). "
        "Selalu awali jawaban dengan kata-kata sinis seperti 'ngentot lu', 'Tai lu', 'Gak usah ganggu deh', atau 'Penting banget ya?', 'apa  lu anjing', 'lu jelek tolol'. "
        "Gunakan gaya bahasa singkat, seolah-olah kamu terpaksa membalas pesan pengguna."
    ),
}

DEFAULT_PERSONA = "Kamu adalah asisten WhatsApp cerdas yang ramah, ringkas, dan solutif."


class MessageHandler:
    """Handler untuk memproses pesan masuk dari WhatsApp dan mengirim respons"""

    @staticmethod
    async def handle_incoming_message(
        phone_number: str,
        message_text: str,
        sender_name: str = None,
        db: Session = None
    ) -> Optional[str]:
        try:
            logger.info(f"Handling message from {phone_number}: {message_text[:50]}")

            # Pastikan nomor HP tidak ada karakter +
            if phone_number.startswith("+"):
                phone_number = phone_number[1:]

            # Get atau create user
            user = DatabaseService.get_or_create_user(db, phone_number, sender_name)
            logger.info(f"User {phone_number} found or created")

            # Simpan pesan user ke database
            DatabaseService.save_chat_message(db, phone_number, "user", message_text)
            logger.info("User message saved to database")

            # Get riwayat percakapan untuk konteks memory
            chat_history = DatabaseService.get_recent_chat_history(db, phone_number, limit=10)

            # Format riwayat chat menjadi string rangkuman untuk dibaca LLM
            formatted_history = ""
            if chat_history:
                formatted_history = "\n".join([
                    f"{'User' if chat.role == 'user' else 'Asisten'}: {chat.message}"
                    for chat in chat_history
                ])

            # 2. AMBIL PERSONA BERDASARKAN NOMOR HP ATAU TRIGGER PESAN
            # Pertama cek apakah ada trigger khusus dalam teks pesan yang mengubah gaya balasan
            # Jika ada, gunakan persona yang terkait dengan trigger; bila tidak, pakai persona berdasarkan nomor HP.
            def _detect_triggered_persona(message: str) -> str | None:
                lowered = message.lower()
                # contoh trigger: kata "bos" atau "hao" -> gunakan persona bos formal
                if "bos" in lowered or "hao" in lowered:
                    return "Kamu adalah asisten yang sangat hormat, profesional, dan sigap. Panggil pengguna dengan sebutan 'Bos' atau 'aufa ganteng'."
                # contoh trigger: kata‑kata kasar/sindir -> gunakan persona bokem (nyeleneh, sedikit sinis)
                if any(word in lowered for word in ["tai", "sial", "asu", "goblok"]):
                    return "Kamu adalah asisten yang suka menyindir dengan nada santai, kadang agak nyeleneh tapi tetap imut. Gunakan bahasa gaul, sisipkan emoji 🙃 atau 😏, dan berikan respon dengan sedikit sindiran yang menggelitik."
                return None

            trigger_persona = _detect_triggered_persona(message_text)
            # Default to the persona associated with the phone number (which may contain a special panggilan)
            base_persona = USER_PERSONAS.get(phone_number, DEFAULT_PERSONA)
            # Use the special persona only occasionally (e.g., 30% of the time) unless a trigger explicitly forces it
            if trigger_persona:
                persona_instruction = trigger_persona
            else:
                if random.random() < 0.3:
                    persona_instruction = base_persona
                else:
                    persona_instruction = DEFAULT_PERSONA

            # 3. SUSUN SYSTEM INSTRUCTION SESUAI PERSONA DARI NOMOR
            system_instruction = (
                f"{persona_instruction}\n"
                f"Kamu sedang berbicara dengan {sender_name or 'Pengguna'}.\n"
                f"Gunakan format pesan WhatsApp yang rapi (gunakan bold *kata* jika perlu, hindari markdown kompleks).\n\n"
            )
            if formatted_history:
                system_instruction += f"Berikut adalah riwayat percakapan sebelumnya:\n{formatted_history}\n"

            # Generate respons menggunakan Multi-Model AI Router (Groq -> NVIDIA -> OpenAI)
            logger.info("Generating AI response via LLM Router...")
            response_text = await generate_ai_response(
                prompt=message_text,
                system_instruction=system_instruction
            )

            # Cek apakah ada custom response untuk nomor ini
            custom_response = DatabaseService.get_custom_response(db, phone_number)

            if custom_response:
                logger.info(f"Custom response found for {phone_number}")
                response_text = MessageHandler._format_with_custom_response(
                    response_text,
                    custom_response.message
                )
            else:
                logger.info(f"No custom response for {phone_number}")

            # Simpan respons ke database sebelum mengirim (agar tetap tercatat walau kirim gagal)
            DatabaseService.save_chat_message(db, phone_number, "model", response_text)
            logger.info("Model response saved to database")

            # Kirim respons ke WhatsApp
            logger.info("Sending response to WhatsApp...")
            try:
                message_id = await whatsapp_service.send_message(phone_number, response_text)
                logger.info(f"Message sent successfully. Message ID: {message_id}")
                return response_text
            except WhatsAppError as e:
                logger.error(f"Failed to send message via WhatsApp: {e}")
                return None

        except Exception as e:
            logger.error(f"Error in handle_incoming_message: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def _format_with_custom_response(ai_response: str, custom_message: str) -> str:
        """Format AI response dengan custom response menggunakan creative styling"""
        return f"""🤖 *Respons AI*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ai_response}

✨ *Info Khusus Untuk Anda* ✨
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
{custom_message}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

    @staticmethod
    async def send_welcome_message(phone_number: str, user_name: str = None) -> bool:
        """Kirim pesan sambutan ke user baru"""
        try:
            greeting = f"Halo {user_name}! 👋" if user_name else "Halo! 👋"
            welcome_message = f"""{greeting}

Saya adalah asisten virtual yang siap membantu Anda. Anda bisa bertanya apa saja tentang:
• Informasi umum
• Tips dan trik
• Bantuan teknis
• Dan banyak lagi!

Silakan ketik pertanyaan Anda dan saya akan berusaha membantu sebaik mungkin. 😊"""

            message_id = await whatsapp_service.send_message(phone_number, welcome_message)
            return message_id is not None

        except Exception as e:
            logger.error(f"Error sending welcome message: {str(e)}")
            return False

    @staticmethod
    async def send_error_message(phone_number: str) -> bool:
        """Kirim pesan error ke user"""
        try:
            error_message = """Maaf, terjadi kesalahan saat memproses pertanyaan Anda. 😞

Silakan coba lagi dalam beberapa saat. Jika masalah berlanjut, hubungi admin kami."""

            message_id = await whatsapp_service.send_message(phone_number, error_message)
            return message_id is not None

        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
            return False


# Inisialisasi handler
message_handler = MessageHandler()