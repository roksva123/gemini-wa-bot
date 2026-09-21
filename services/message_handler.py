import logging
from sqlalchemy.orm import Session
from database import DatabaseService
from services.gemini import gemini_service
from services.whatsapp import whatsapp_service, WhatsAppError
from typing import Optional

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handler untuk memproses pesan masuk dari WhatsApp dan mengirim respons"""

    @staticmethod
    async def handle_incoming_message(
        phone_number: str,
        message_text: str,
        sender_name: str = None,
        db: Session = None
    ) -> Optional[str]:
        """
        Handle pesan masuk dari WhatsApp

        Args:
            phone_number: Nomor HP pengirim (tanpa tanda + di depan)
            message_text: Teks pesan yang masuk
            sender_name: Nama pengirim (opsional)
            db: Database session

        Returns:
            Pesan respons yang akan dikirim
        """
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
            logger.info(f"User message saved to database")

            # Get riwayat percakapan untuk konteks
            chat_history = DatabaseService.get_recent_chat_history(db, phone_number, limit=10)

            # Convert to dict format
            history_list = [
                {
                    "role": chat.role,
                    "message": chat.message
                }
                for chat in chat_history
            ]

            # Generate respons menggunakan Gemini
            logger.info(f"Generating Gemini response...")
            response_text = await gemini_service.generate_response_with_history(
                message_text,
                history_list
            )

            # Cek apakah ada custom response untuk nomor ini
            custom_response = DatabaseService.get_custom_response(db, phone_number)

            if custom_response:
                logger.info(f"Custom response found for {phone_number}")
                # Format dengan creative styling
                response_text = MessageHandler._format_with_custom_response(
                    response_text,
                    custom_response.message
                )
            else:
                logger.info(f"No custom response for {phone_number}")

            # Simpan respons ke database **before** mengirim (agar tetap tercatat walau kirim gagal)
            DatabaseService.save_chat_message(db, phone_number, "model", response_text)
            logger.info(f"Model response saved to database")

            # Kirim respons ke WhatsApp
            logger.info(f"Sending response to WhatsApp...")
            try:
                message_id = await whatsapp_service.send_message(phone_number, response_text)
                logger.info(f"Message sent successfully. Message ID: {message_id}")
                return response_text
            except WhatsAppError as e:
                logger.error(f"Failed to send message via WhatsApp: {e}")
                # Optional: flag the DB record as unsent or schedule retry
                return None

        except Exception as e:
            logger.error(f"Error in handle_incoming_message: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def _format_with_custom_response(ai_response: str, custom_message: str) -> str:
        """
        Format AI response dengan custom response menggunakan creative styling

        Args:
            ai_response: Respons dari AI
            custom_message: Custom message dari database

        Returns:
            Formatted message dengan emoji, lines, dan tildes
        """
        formatted = f"""🤖 *Respons AI*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ai_response}

✨ *Info Khusus Untuk Anda* ✨
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
{custom_message}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

        return formatted

    @staticmethod
    async def send_welcome_message(phone_number: str, user_name: str = None) -> bool:
        """
        Kirim pesan sambutan ke user baru

        Args:
            phone_number: Nomor HP user
            user_name: Nama user

        Returns:
            True jika berhasil, False jika gagal
        """
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
        """
        Kirim pesan error ke user

        Args:
            phone_number: Nomor HP user

        Returns:
            True jika berhasil, False jika gagal
        """
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
