import logging
import json
from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db, create_tables, DatabaseService
from services.whatsapp import whatsapp_service
from services.message_handler import message_handler

# =====================================================
# Development Dependency (placeholder)
# =====================================================

def require_development():
    """Placeholder dependency to allow development-only endpoints.
    Currently a no-op; can be extended to restrict access in production.
    """
    return None


# =====================================================
# Konfigurasi Logging
# =====================================================
logging.basicConfig(
    level=settings.normalized_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =====================================================
# Inisialisasi FastAPI App
# =====================================================
app = FastAPI(
    title=settings.app_name,
    description="Bot WhatsApp berbasis AI Gemini dengan memory percakapan",
    version="1.0.0"
)

# =====================================================
# Startup Event
# =====================================================
@app.on_event("startup")
async def startup_event():
    """Jalankan setup saat aplikasi startup"""
    logger.info("Aplikasi sedang startup...")

    # Buat tabel database jika belum ada
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

    logger.info(f"Bot WhatsApp AI siap di: http://localhost:{settings.port}")


# =====================================================
# Health Check Endpoint
# =====================================================
@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint untuk mengecek status aplikasi"""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "1.0.0"
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
    """
    Endpoint untuk verifikasi webhook dari WhatsApp

    WhatsApp akan mengirim GET request dengan:
    - hub.mode: "subscribe"
    - hub.challenge: challenge string
    - hub.verify_token: token untuk verifikasi
    """
    logger.info("Webhook verification request received")
    safe_token = f"{hub_verify_token[:10]}..." if hub_verify_token else "<missing>"
    logger.info(f"Mode: {hub_mode}, Token: {safe_token}")

    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="Invalid hub mode")

    # Verifikasi token
    if whatsapp_service.verify_webhook_token(hub_verify_token):
        logger.info("Webhook verified successfully")
        return hub_challenge

    logger.error("Invalid webhook token")
    raise HTTPException(status_code=403, detail="Invalid verify token")


@app.post("/webhook", tags=["Webhook"])
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint untuk menerima pesan dari WhatsApp

    WhatsApp akan mengirim POST request dengan struktur:
    {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "...",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {...},
                            "contacts": [...],
                            "messages": [...]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    """
    try:
        # Parse request body
        body = await request.json()
        logger.info(f"Webhook request received: {json.dumps(body, indent=2)[:500]}")

        # Validasi struktur
        if body.get("object") != "whatsapp_business_account":
            logger.warning(f"Invalid object type: {body.get('object')}")
            return JSONResponse(status_code=200, content={"status": "ok"})

        # Proses setiap entry
        entries = body.get("entry") or []
        if not isinstance(entries, list):
            logger.warning("Invalid entry payload")
            return JSONResponse(status_code=200, content={"status": "ok"})

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
                            response = await message_handler.handle_incoming_message(
                                phone_number=phone_number,
                                message_text=message_text,
                                sender_name=sender_name,
                                db=db
                            )

                            if not response:
                                # Jika ada error, kirim pesan error
                                await message_handler.send_error_message(phone_number)
                        else:
                            logger.info(f"Skipping non-text message type: {message_type}")

                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}", exc_info=True)
                        continue

        # Return 200 OK untuk acknowledge webhook
        return JSONResponse(status_code=200, content={"status": "ok"})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})
    except Exception as e:
        logger.error(f"Error in handle_webhook: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


# =====================================================
# Debug Endpoints (opsional, untuk testing)
# =====================================================
@app.post("/test/send-message", dependencies=[Depends(require_development)])
async def test_send_message(
    phone_number: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk testing pengiriman pesan manual

    Hanya gunakan untuk development!
    """
    try:
        logger.info(f"Test: Sending message to {phone_number}: {message}")

        # Pastikan nomor HP valid
        if not phone_number or len(phone_number) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")

        # Kirim pesan
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


@app.get("/test/chat-history/{phone_number}", tags=["Debug"])
async def test_get_chat_history(phone_number: str, db: Session = Depends(get_db)):
    """
    Endpoint untuk melihat riwayat chat seorang user

    Hanya untuk development!
    """
    try:
        from database import DatabaseService

        history = DatabaseService.get_recent_chat_history(db, phone_number, limit=20)

        if not history:
            return {
                "phone_number": phone_number,
                "message_count": 0,
                "messages": []
            }

        messages = [
            {
                "role": chat.role,
                "message": chat.message,
                "timestamp": chat.created_at.isoformat()
            }
            for chat in history
        ]

        return {
            "phone_number": phone_number,
            "message_count": len(messages),
            "messages": messages
        }

    except Exception as e:
        logger.error(f"Error in test chat history endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Custom Response Management Endpoints
# =====================================================
@app.get("/custom-response/{phone_number}", tags=["Custom Response"])
async def get_custom_response(phone_number: str, db: Session = Depends(get_db)):
    """
    Dapatkan custom response untuk nomor telepon tertentu
    """
    try:
        logger.info(f"Getting custom response for {phone_number}")

        custom_response = DatabaseService.get_custom_response(db, phone_number)

        if not custom_response:
            return {
                "phone_number": phone_number,
                "found": False,
                "message": None
            }

        return {
            "phone_number": phone_number,
            "found": True,
            "message": custom_response.message,
            "created_at": custom_response.created_at.isoformat(),
            "updated_at": custom_response.updated_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting custom response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/custom-response", tags=["Custom Response"])
async def create_or_update_custom_response(
    phone_number: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    Tambah atau update custom response untuk nomor telepon

    Query parameters:
    - phone_number: Nomor telepon (misal: 62812345678)
    - message: Custom message yang akan di-append ke AI response
    """
    try:
        logger.info(f"Creating/updating custom response for {phone_number}")

        if not phone_number or len(phone_number) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")

        if not message or len(message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Simpan atau update custom response
        custom_response = DatabaseService.save_or_update_custom_response(
            db, phone_number, message
        )

        return {
            "success": True,
            "phone_number": phone_number,
            "message": custom_response.message,
            "created_at": custom_response.created_at.isoformat(),
            "updated_at": custom_response.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving custom response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/custom-response/{phone_number}", tags=["Custom Response"])
async def delete_custom_response(phone_number: str, db: Session = Depends(get_db)):
    """
    Hapus custom response untuk nomor telepon tertentu
    """
    try:
        logger.info(f"Deleting custom response for {phone_number}")

        from database import CustomResponse

        custom_response = db.query(CustomResponse).filter(
            CustomResponse.phone_number == phone_number
        ).first()

        if not custom_response:
            raise HTTPException(status_code=404, detail="Custom response not found")

        db.delete(custom_response)
        db.commit()

        logger.info(f"Custom response deleted for {phone_number}")

        return {
            "success": True,
            "message": "Custom response deleted successfully",
            "phone_number": phone_number
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting custom response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
