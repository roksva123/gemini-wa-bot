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

    # Daftar versi Graph API yang akan dicoba bila versi default gagal
    _fallback_api_versions = ["v19.0", "v18.0", "v15.0", "v14.0"]

    def __init__(self):
        """Inisialisasi WhatsApp API client"""
        self.phone_number_id = settings.wa_phone_number_id
        self.access_token = settings.wa_access_token
        # API version can be configured via env (default 18). We ensure the version
        # string follows the pattern "vXX.0" required by the Graph API.
        raw_version = getattr(settings, "wa_api_version", "18")
        # Strip any leading "v" and trailing ".0" to normalize
        clean_version = str(raw_version).lstrip("v").rstrip(".0")
        self.api_version = f"v{clean_version}.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"


    # ------------------------------------------------------------------
    # Helper: bangun URL lengkap dengan versi API yang ingin dicoba
    # ------------------------------------------------------------------
    def _url_with_version(self, version: str) -> str:
        return f"https://graph.facebook.com/{version}/{self.phone_number_id}"

    async def send_message(self, phone_number: str, message_text: str) -> Optional[str]:
        """Kirim pesan teks ke nomor WhatsApp tertentu.

        Mencoba beberapa versi API jika versi pertama menghasilkan error.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"preview_url": False, "body": message_text},
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        # Coba tiap versi API secara berurutan
        for version in [self.api_version] + self._fallback_api_versions:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self._url_with_version(version)}/messages",
                        json=payload,
                        headers=headers,
                        timeout=30.0,
                    )
                if response.status_code == 200:
                    data = response.json()
                    message_id = data.get("messages", [{}])[0].get("id")
                    logger.info(
                        f"Message sent successfully to {phone_number} via API {version}. Message ID: {message_id}"
                    )
                    return message_id
                # Jika bukan 200, log error dan coba versi berikutnya
                logger.error(
                    f"Failed to send message via API {version}. Status: {response.status_code}, Response: {response.text}"
                )
            except Exception as e:
                logger.error(
                    f"Exception while sending message via API {version}: {e}", exc_info=True
                )
        # Semua versi gagal → raise agar caller dapat menanganinya
        raise WhatsAppError(
            f"All API versions failed to send message to {phone_number}."
        )

    async def mark_as_read(self, message_id: str) -> bool:
        """Tandai pesan sebagai sudah dibaca. Tries multiple API versions."""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        for version in [self.api_version] + self._fallback_api_versions:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self._url_with_version(version)}/messages",
                        json=payload,
                        headers=headers,
                        timeout=30.0,
                    )
                if response.status_code == 200:
                    logger.info(f"Message {message_id} marked as read via API {version}")
                    return True
                logger.error(
                    f"Failed to mark message as read via API {version}. Status: {response.status_code}"
                )
            except Exception as e:
                logger.error(
                    f"Exception while marking read via API {version}: {e}", exc_info=True
                )
        logger.error(f"All API versions failed to mark message {message_id} as read.")
        return False


    def verify_webhook_token(self, token: str) -> bool:
        """Verifikasi token webhook dari WhatsApp"""
        return token == settings.wa_verify_token


# Inisialisasi singleton instance
whatsapp_service = WhatsAppService()
