import logging
import json
from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import get_db, create_tables
from services.whatsapp import whatsapp_service
from services.message_handler import message_handler
from services.rate_limiter import RateLimitMiddleware
from routers.admin import router as admin_router

# Konfigurasi Logging
logging.basicConfig(
    level=settings.normalized_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Pydantic model untuk test endpoint
class TestMessageRequest(BaseModel):
    """Schema untuk /test/send-message endpoint"""
    phone_number: str
    message: str


# Inisialisasi FastAPI App
app = FastAPI(
    title=settings.app_name,
    description="Multi-client WhatsApp Bot berbasis AI Gemini",
    version="2.0.0",
)

# Setup Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include admin router
app.include_router(admin_router)


# =====================================================
# Health Check Endpoint
# =====================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint untuk mengecek status aplikasi"""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "2.0.0"
    }


# =====================================================
# WhatsApp Webhook Endpoints
# =====================================================

@app.get("/webhook", tags=["Webhook"])
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Endpoint untuk verifikasi webhook dari WhatsApp"""
    logger.info("Webhook verification request received")
    safe_token = f"{hub_verify_token[:10]}..." if hub_verify_token else "<missing>"
    logger.info(f"Mode: {hub_mode}, Token: {safe_token}")

    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="Invalid hub mode")

    # Verifikasi token
    if whatsapp_service.verify_webhook_token(hub_verify_token):
        logger.info("Webhook verified successfully")
        return Response(content=str(hub_challenge), media_type="text/plain")

    logger.error("Invalid webhook token")
    raise HTTPException(status_code=403, detail="Invalid verify token")


@app.post("/webhook", tags=["Webhook"])
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint untuk menerima pesan dari WhatsApp

    WhatsApp akan mengirim POST request dengan struktur:
    {
        "object": "whatsapp_business_account",
        "entry": [...]
    }
    """
    try:
        body = await request.json()
        logger.info("Webhook request received: %s", json.dumps(body, indent=2))

        # Validasi struktur
        if body.get("object") != "whatsapp_business_account":
            logger.warning(f"Invalid object type: {body.get('object')}")
            return {"status": "ok"}

        # Proses setiap entry
        entries = body.get("entry") or []
        if not isinstance(entries, list):
            logger.warning("Invalid entry payload")
            return {"status": "ok"}

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            changes = entry.get("changes") or []
            if not isinstance(changes, list):
                continue

            for change in changes:
                if not isinstance(change, dict):
                    continue

                # Hanya proses changes untuk messages
                if change.get("field") != "messages":
                    continue

                value = change.get("value") or {}
                if not isinstance(value, dict):
                    continue

                messages = value.get("messages") or []
                contacts = value.get("contacts") or []

                if not isinstance(messages, list):
                    continue
                if not isinstance(contacts, list):
                    contacts = []

                # Proses setiap pesan
                for message in messages:
                    try:
                        if not isinstance(message, dict):
                            continue

                        phone_number = message.get("from")
                        message_id = message.get("id")
                        message_type = message.get("type", "text")

                        # Ambil nama pengirim dari contacts
                        sender_name = None
                        if contacts:
                            sender_name = contacts[0].get("profile", {}).get("name")

                        logger.info(f"Processing message from {phone_number}: type={message_type}")

                        # Hanya proses pesan teks
                        if message_type == "text":
                            text_content = message.get("text", {})
                            message_text = text_content.get("body", "").strip()

                            if not message_text:
                                logger.warning("Empty message text")
                                continue

                            logger.info(f"Message text: {message_text[:100]}")

                            # Tandai pesan sebagai read
                            await whatsapp_service.mark_as_read(message_id)

                            # Handle pesan dengan AI
                            # Business akan di-detect dari nomor WhatsApp di database
                            response = await message_handler.handle_incoming_message(
                                phone_number=phone_number,
                                message_text=message_text,
                                sender_name=sender_name,
                                db=db
                            )

                            if not response:
                                logger.warning(f"No response generated for {phone_number}")
                        else:
                            logger.info(f"Skipping non-text message type: {message_type}")

                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}", exc_info=True)
                        continue

        return {"status": "ok"}

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return {"error": "Invalid JSON"}
    except Exception as e:
        logger.error(f"Error in handle_webhook: {str(e)}", exc_info=True)
        return {"error": str(e)}


# =====================================================
# Debug Endpoints (development only)
# =====================================================

@app.post("/test/send-message", tags=["Debug"])
async def test_send_message(
    request_body: TestMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk testing pengiriman pesan manual (JSON body)
    Hanya gunakan untuk development!
    """
    try:
        phone_number = request_body.phone_number
        message = request_body.message

        logger.info(f"Test: Sending message to {phone_number}: {message}")

        if not phone_number or len(phone_number) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")

        message_id = await whatsapp_service.send_message(phone_number, message)

        if message_id:
            return {
                "success": True,
                "message_id": message_id,
                "phone_number": phone_number
            }
        else:
            return {
                "success": False,
                "error": "Failed to send message"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/chat-history/{conversation_id}", tags=["Debug"])
async def test_get_chat_history(conversation_id: int, db: Session = Depends(get_db)):
    """
    Endpoint untuk melihat riwayat chat dari conversation (untuk development)
    """
    try:
        from database import DatabaseService
        from models import Conversation, ChatMessage

        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return {
                "conversation_id": conversation_id,
                "found": False,
                "message_count": 0,
                "messages": []
            }

        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at.asc()).all()

        result_messages = [
            {
                "role": msg.role,
                "message": msg.message,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]

        return {
            "conversation_id": conversation_id,
            "customer_phone": conversation.customer_phone,
            "customer_name": conversation.customer_name,
            "found": True,
            "message_count": len(result_messages),
            "messages": result_messages
        }

    except Exception as e:
        logger.error(f"Error in test chat history endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Startup Events
# =====================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")


# =====================================================
# Main Entry Point
# =====================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
