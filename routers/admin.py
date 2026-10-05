"""
Admin Router untuk endpoints admin
Semua endpoint dilindungi dengan JWT authentication
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import bcrypt

from database import get_db, DatabaseService
from schemas import (
    AdminLoginRequest, AdminLoginResponse, TokenData,
    BusinessResponse, BusinessCreate, BusinessUpdate,
    FAQResponse, FAQCreate, FAQUpdate,
    ConversationResponse, ConversationDetailResponse, ConversationHandoffRequest, ConversationReplyRequest,
    LeadResponse, LeadUpdate,
    TestChatRequest, TestChatResponse,
    ErrorResponse
)
from config import settings
from models import AdminUser, Business, FAQ, Conversation, Lead, ChatMessage
from services.message_handler import message_handler
from services.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Admin"])


# =====================================================
# Auth Utilities
# =====================================================

def hash_password(password: str) -> str:
    """Hash password dengan bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password dengan bcrypt"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(business_id: int, admin_user_id: int) -> str:
    """Buat JWT token"""
    payload = {
        "business_id": business_id,
        "admin_user_id": admin_user_id,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def verify_token(authorization: Optional[str] = Header(None)) -> TokenData:
    """Verify JWT token dari Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    # Extract token dari "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    token = parts[1]

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        business_id: int = payload.get("business_id")
        admin_user_id: int = payload.get("admin_user_id")

        if business_id is None or admin_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return TokenData(business_id=business_id, admin_user_id=admin_user_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# =====================================================
# Auth Endpoints
# =====================================================

@router.post("/auth/login", response_model=AdminLoginResponse)
async def login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    Login admin menggunakan email dan password
    Returns: JWT token untuk digunakan di request selanjutnya
    """
    try:
        # Cari admin user
        admin_user = db.query(AdminUser).filter(
            AdminUser.email == request.email
        ).first()

        if not admin_user:
            logger.warning(f"Login attempt dengan email tidak terdaftar: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email atau password salah"
            )

        # Verify password
        if not verify_password(request.password, admin_user.password_hash):
            logger.warning(f"Login attempt dengan password salah untuk: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email atau password salah"
            )

        if not admin_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akun admin tidak aktif"
            )

        # Generate token
        access_token = create_access_token(admin_user.business_id, admin_user.id)
        logger.info(f"Admin {request.email} login berhasil")

        return AdminLoginResponse(
            access_token=access_token,
            token_type="bearer",
            business_id=admin_user.business_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =====================================================
# Business Endpoints
# =====================================================

@router.get("/business", response_model=BusinessResponse)
async def get_business(
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Dapatkan data bisnis untuk admin yang login"""
    business = DatabaseService.get_business_by_id(db, token.business_id)

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return BusinessResponse.from_orm(business)


@router.put("/business", response_model=BusinessResponse)
async def update_business(
    request: BusinessUpdate,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update data bisnis"""
    business = db.query(Business).filter(Business.id == token.business_id).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Update fields yang dikirim
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(business, field, value)

    db.commit()
    db.refresh(business)

    logger.info(f"Business {token.business_id} updated")
    return BusinessResponse.from_orm(business)


# =====================================================
# FAQ Endpoints
# =====================================================

@router.get("/faqs", response_model=List[FAQResponse])
async def get_faqs(
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Dapatkan semua FAQ untuk bisnis"""
    faqs = DatabaseService.get_faqs_for_business(db, token.business_id)
    return [FAQResponse.from_orm(faq) for faq in faqs]


@router.post("/faqs", response_model=FAQResponse)
async def create_faq(
    request: FAQCreate,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Buat FAQ baru"""
    faq = FAQ(
        business_id=token.business_id,
        question=request.question,
        answer=request.answer,
        order=request.order
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)

    logger.info(f"FAQ {faq.id} created for business {token.business_id}")
    return FAQResponse.from_orm(faq)


@router.put("/faqs/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    request: FAQUpdate,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update FAQ"""
    faq = db.query(FAQ).filter(
        FAQ.id == faq_id,
        FAQ.business_id == token.business_id
    ).first()

    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(faq, field, value)

    db.commit()
    db.refresh(faq)

    logger.info(f"FAQ {faq_id} updated")
    return FAQResponse.from_orm(faq)


@router.delete("/faqs/{faq_id}")
async def delete_faq(
    faq_id: int,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Hapus FAQ"""
    faq = db.query(FAQ).filter(
        FAQ.id == faq_id,
        FAQ.business_id == token.business_id
    ).first()

    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.delete(faq)
    db.commit()

    logger.info(f"FAQ {faq_id} deleted")
    return {"success": True}


# =====================================================
# Conversation Endpoints
# =====================================================

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Dapatkan daftar percakapan untuk bisnis"""
    conversations = db.query(Conversation).filter(
        Conversation.business_id == token.business_id
    ).order_by(
        Conversation.updated_at.desc()
    ).offset(offset).limit(limit).all()

    return [ConversationResponse.from_orm(conv) for conv in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: int,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Dapatkan detail percakapan dengan message history"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.business_id == token.business_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id
    ).order_by(ChatMessage.created_at.asc()).all()

    result = ConversationDetailResponse.from_orm(conversation)
    result.messages = [ChatMessageResponse.from_orm(msg) for msg in messages]

    return result


@router.post("/conversations/{conversation_id}/handoff", response_model=ConversationResponse)
async def set_conversation_handoff(
    conversation_id: int,
    request: ConversationHandoffRequest,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Set handoff status untuk percakapan"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.business_id == token.business_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.handoff = request.handoff
    db.commit()
    db.refresh(conversation)

    status_text = "admin handoff" if request.handoff else "bot active"
    logger.info(f"Conversation {conversation_id} set to {status_text}")

    return ConversationResponse.from_orm(conversation)


@router.post("/conversations/{conversation_id}/reply")
async def reply_to_conversation(
    conversation_id: int,
    request: ConversationReplyRequest,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin membalas percakapan secara manual"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.business_id == token.business_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Kirim pesan dan simpan ke database
    success = await message_handler.send_admin_reply(
        phone_number=conversation.customer_phone,
        message_text=request.message,
        db=db,
        conversation_id=conversation_id
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message")

    logger.info(f"Admin reply sent to conversation {conversation_id}")
    return {"success": True}


# =====================================================
# Lead Endpoints
# =====================================================

@router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 100
):
    """Dapatkan leads untuk bisnis"""
    leads = DatabaseService.get_leads_for_business(db, token.business_id, status)[:limit]
    return [LeadResponse.from_orm(lead) for lead in leads]


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    request: LeadUpdate,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update status lead"""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.business_id == token.business_id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    logger.info(f"Lead {lead_id} updated to status {lead.status}")
    return LeadResponse.from_orm(lead)


# =====================================================
# Test Chat Endpoint
# =====================================================

@router.post("/chat/test", response_model=TestChatResponse)
async def test_chat(
    request: TestChatRequest,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Test bot response tanpa WhatsApp
    Digunakan di halaman "Coba Bot" admin
    """
    try:
        # Ambil business dan FAQs
        business = DatabaseService.get_business_by_id(db, token.business_id)
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        faqs = DatabaseService.get_faqs_for_business(db, token.business_id)

        # Build system prompt
        system_instruction = build_system_prompt(business, faqs)

        # Generate response
        from services.llm_router import generate_ai_response

        messages = [{"role": "user", "content": request.message}]
        response_text = await generate_ai_response(
            messages=messages,
            system_instruction=system_instruction
        )

        if not response_text:
            return TestChatResponse(success=False, error="No response from AI")

        logger.info(f"Test chat completed for business {token.business_id}")
        return TestChatResponse(success=True, message=response_text)

    except Exception as e:
        logger.error(f"Error in test chat: {str(e)}")
        return TestChatResponse(
            success=False,
            error=f"Error: {str(e)}"
        )


# Import untuk type hints di decorator
from schemas import ChatMessageResponse
