import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


class WhatsAppError(RuntimeError):
    """Custom exception for WhatsApp service errors"""
    pass


class WhatsAppService:
    """Service untuk integrasi dengan WhatsApp Cloud API"""

    def __init__(self):
        """Inisialisasi WhatsApp API client"""
        self.phone_number_id = settings.wa_phone_number_id
        self.access_token = settings.wa_access_token
        # API version can be configured via env (default 18)
        self.api_version = settings.wa_api_version
        self.base_url = f"https://graph.facebook.com/v{self.api_version}/{self.phone_number_id}"

    async def send_message(self, phone_number: str, message_text: str) -> Optional[str]:
        """Kirim pesan teks ke nomor WhatsApp tertentu.

        Returns the message ID on success or raises ``WhatsAppError`` on failure.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"preview_url": False, "body": message_text},
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                logger.info(
                    f"Message sent successfully to {phone_number}. Message ID: {message_id}"
                )
                return message_id
            # Return detailed error info instead of None
            error_detail = f"Status: {response.status_code}, Response: {response.text}"
            logger.error(f"Failed to send message. {error_detail}")
            raise WhatsAppError(error_detail)
        except httpx.TimeoutException:
            logger.error(f"Timeout while sending message to {phone_number}")
            raise WhatsAppError("Timeout while sending message")
        except Exception as e:
            logger.error(f"Error sending message to {phone_number}: {str(e)}")
            raise WhatsAppError(str(e))

    async def mark_as_read(self, message_id: str) -> bool:
        """Tandai pesan sebagai sudah dibaca. Returns ``True`` on success."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
            if response.status_code == 200:
                logger.info(f"Message {message_id} marked as read")
                return True
            logger.error(f"Failed to mark message as read. Status: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False

    def verify_webhook_token(self, token: str) -> bool:
        """Verifikasi token webhook dari WhatsApp"""
        return token == settings.wa_verify_token


# Inisialisasi singleton instance
whatsapp_service = WhatsAppService()
