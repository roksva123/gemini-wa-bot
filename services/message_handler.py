"""
Message Handler untuk memproses pesan masuk dari WhatsApp
Menangani logika percakapan, deteksi intent, dan routing ke LLM
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import DatabaseService
from services.llm_router import generate_ai_response
from services.whatsapp import whatsapp_service, WhatsAppError
from services.prompt_builder import (
    build_system_prompt,
    validate_message_length,
    detect_order_intent
)
from config import settings

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handler untuk memproses pesan masuk dari WhatsApp dan mengirim respons"""

    @staticmethod
    async def handle_incoming_message(
        phone_number: str,
        message_text: str,
        sender_name: str = None,
        db: Session = None,
        business_id: int = None
    ) -> Optional[str]:
        """
        Handle pesan masuk dari WhatsApp

        Args:
            phone_number: Nomor WhatsApp pengirim (tanpa +)
            message_text: Isi pesan
            sender_name: Nama pengirim (dari WhatsApp)
            db: Database session
            business_id: ID bisnis (opsional, akan di-detect dari WA number jika tidak ada)

        Returns:
            Respons yang dikirim, atau None jika error
        """
        try:
            logger.info(f"Handling message from {phone_number}: {message_text[:50]}")

            # Normalize phone number (hapus + jika ada)
            if phone_number.startswith("+"):
                phone_number = phone_number[1:]

            # Validasi panjang pesan
            is_valid, error_msg = validate_message_length(
                message_text,
                max_length=settings.max_message_length
            )
            if not is_valid:
                logger.warning(f"Invalid message length from {phone_number}: {error_msg}")
                await whatsapp_service.send_message(phone_number, error_msg)
                return None

            # =====================================================
            # Tentukan Business dari nomor WA tujuan
            # =====================================================
            if not business_id:
                business = DatabaseService.get_business_by_whatsapp(db, phone_number)
                if not business:
                    logger.warning(f"No business found for WhatsApp number {phone_number}")
                    await whatsapp_service.send_message(
                        phone_number,
                        "Maaf, nomor ini belum terdaftar. Hubungi administrator."
                    )
                    return None
                business_id = business.id
            else:
                business = DatabaseService.get_business_by_id(db, business_id)
                if not business:
                    logger.error(f"Business {business_id} not found")
                    return None

            # =====================================================
            # Ambil atau buat Conversation
            # =====================================================
            conversation = DatabaseService.get_or_create_conversation(
                db,
                business_id=business_id,
                customer_phone=phone_number,
                customer_name=sender_name
            )
            logger.info(f"Conversation {conversation.id} for {phone_number}")

            # =====================================================
            # Simpan pesan user ke database
            # =====================================================
            DatabaseService.save_chat_message(
                db,
                conversation_id=conversation.id,
                role="user",
                message=message_text
            )
            logger.info("User message saved to database")

            # =====================================================
            # BUG FIX #5: Cek handoff status
            # Jika conversation.handoff == True, JANGAN panggil LLM
            # =====================================================
            if conversation.handoff:
                logger.info(f"Conversation {conversation.id} is in handoff mode. Skipping LLM.")
                # Simpan pesan tapi tidak generate respons
                return None

            # =====================================================
            # Ambil riwayat percakapan (10 pesan terakhir)
            # BUG FIX #5: Convert ke format messages array
            # =====================================================
            chat_history = DatabaseService.get_recent_chat_history(
                db,
                conversation_id=conversation.id,
                limit=10
            )
            logger.info(f"Retrieved {len(chat_history)} messages from history")

            # =====================================================
            # BUG FIX #1, #2, #6: Build system prompt dari Business + FAQ
            # =====================================================
            faqs = DatabaseService.get_faqs_for_business(db, business_id)
            system_instruction = build_system_prompt(business, faqs)
            logger.info(f"System prompt built for business {business.name}")

            # =====================================================
            # BUG FIX #5: Kirim messages array (bukan string history)
            # =====================================================
            logger.info("Generating AI response via LLM Router...")
            response_text = await generate_ai_response(
                messages=chat_history,  # Array of {"role": "user", "content": "..."}
                system_instruction=system_instruction
            )

            if not response_text:
                logger.error("LLM Router returned empty response")
                await whatsapp_service.send_message(
                    phone_number,
                    "Maaf, terjadi kesalahan saat memproses pertanyaan Anda. Silakan coba lagi."
                )
                return None

            # =====================================================
            # BUG FIX #4: Deteksi Lead untuk intent pemesanan
            # =====================================================
            if detect_order_intent(message_text, faqs):
                logger.info(f"Order intent detected from {phone_number}")
                # Buat atau update Lead
                DatabaseService.create_lead(
                    db,
                    business_id=business_id,
                    customer_name=sender_name or conversation.customer_name or "Unknown",
                    customer_phone=phone_number,
                    need=message_text
                )
                logger.info("Lead created/updated")

            # =====================================================
            # Simpan respons ke database SEBELUM kirim
            # =====================================================
            DatabaseService.save_chat_message(
                db,
                conversation_id=conversation.id,
                role="assistant",
                message=response_text
            )
            logger.info("AI response saved to database")

            # =====================================================
            # BUG FIX #6: Kirim respons tanpa header dekoratif
            # =====================================================
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
    async def send_welcome_message(phone_number: str, user_name: str = None) -> bool:
        """Kirim pesan sambutan ke user baru"""
        try:
            greeting = f"Halo {user_name}! 👋" if user_name else "Halo! 👋"
            welcome_message = f"""{greeting}

Saya adalah asisten virtual yang siap membantu Anda. Anda bisa bertanya tentang produk, layanan, atau kebutuhan Anda.

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

    @staticmethod
    async def send_admin_reply(
        phone_number: str,
        message_text: str,
        db: Session = None,
        conversation_id: int = None
    ) -> bool:
        """
        Kirim balasan admin manual ke customer

        Args:
            phone_number: Nomor customer
            message_text: Pesan dari admin
            db: Database session
            conversation_id: ID percakapan (untuk update ke database)
        """
        try:
            # Kirim pesan
            message_id = await whatsapp_service.send_message(phone_number, message_text)

            if message_id and db and conversation_id:
                # Simpan ke database sebagai assistant message
                DatabaseService.save_chat_message(
                    db,
                    conversation_id=conversation_id,
                    role="assistant",
                    message=message_text
                )

            return message_id is not None

        except Exception as e:
            logger.error(f"Error sending admin reply: {str(e)}")
            return False


# Inisialisasi handler
message_handler = MessageHandler()
