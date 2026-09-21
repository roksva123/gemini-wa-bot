from pydantic import BaseModel, Field
from typing import Optional, List


# =====================================================
# WhatsApp Webhook Models
# =====================================================

class WebhookEntry(BaseModel):
    """Model untuk entry di webhook WhatsApp"""
    id: str
    changes: List[dict]


class WebhookMessage(BaseModel):
    """Model untuk pesan yang diterima dari WhatsApp"""
    object: str
    entry: List[WebhookEntry]


class WhatsAppContact(BaseModel):
    """Model untuk kontak pengirim"""
    profile: dict
    wa_id: str


class WhatsAppMessage(BaseModel):
    """Model untuk struktur pesan WhatsApp"""
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    text: Optional[dict] = None
    type: str

    class Config:
        populate_by_name = True


class WhatsAppValue(BaseModel):
    """Model untuk value di dalam changes"""
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessage]] = None
    messaging_product: Optional[str] = None
    metadata: Optional[dict] = None


class WhatsAppChange(BaseModel):
    """Model untuk change di dalam entry"""
    value: WhatsAppValue
    field: str


# =====================================================
# Gemini AI Models
# =====================================================

class GeminiMessage(BaseModel):
    """Model untuk pesan dalam format Gemini"""
    role: str  # "user" atau "model"
    parts: List[dict]  # [{"text": "..."}]


class ChatMessage(BaseModel):
    """Model untuk pesan chat"""
    role: str
    message: str


# =====================================================
# Response Models
# =====================================================

class MessageResponse(BaseModel):
    """Response untuk pengiriman pesan"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class UserResponse(BaseModel):
    """Response untuk data user"""
    phone_number: str
    name: Optional[str] = None
    created_at: str
