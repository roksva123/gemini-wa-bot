"""
Pydantic schemas untuk request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# =====================================================
# Auth Schemas
# =====================================================

class AdminLoginRequest(BaseModel):
    """Request untuk login admin"""
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    """Response untuk login admin"""
    access_token: str
    token_type: str = "bearer"
    business_id: int


class TokenData(BaseModel):
    """Data yang ada di JWT token"""
    business_id: int
    admin_user_id: int


# =====================================================
# Business Schemas
# =====================================================

class BusinessBase(BaseModel):
    """Base model untuk Business"""
    name: str
    category: Optional[str] = None
    tone: str = "ramah"  # ramah, formal, profesional, santai
    opening_hours: Optional[str] = None
    address: Optional[str] = None
    order_flow: Optional[str] = None


class BusinessCreate(BusinessBase):
    """Request untuk create business"""
    whatsapp_number: str


class BusinessUpdate(BaseModel):
    """Request untuk update business"""
    name: Optional[str] = None
    category: Optional[str] = None
    tone: Optional[str] = None
    opening_hours: Optional[str] = None
    address: Optional[str] = None
    order_flow: Optional[str] = None
    is_active: Optional[bool] = None


class BusinessResponse(BusinessBase):
    """Response untuk business"""
    id: int
    whatsapp_number: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# FAQ Schemas
# =====================================================

class FAQBase(BaseModel):
    """Base model untuk FAQ"""
    question: str
    answer: str
    order: int = 0


class FAQCreate(FAQBase):
    """Request untuk create FAQ"""
    pass


class FAQUpdate(BaseModel):
    """Request untuk update FAQ"""
    question: Optional[str] = None
    answer: Optional[str] = None
    order: Optional[int] = None


class FAQResponse(FAQBase):
    """Response untuk FAQ"""
    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# Conversation & Message Schemas
# =====================================================

class ChatMessageResponse(BaseModel):
    """Response untuk chat message"""
    id: int
    role: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Response untuk conversation"""
    id: int
    business_id: int
    customer_phone: str
    customer_name: Optional[str] = None
    handoff: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Response detail conversation dengan messages"""
    messages: List[ChatMessageResponse] = []


class ConversationHandoffRequest(BaseModel):
    """Request untuk set handoff status"""
    handoff: bool


class ConversationReplyRequest(BaseModel):
    """Request untuk admin membalas manual"""
    message: str


# =====================================================
# Lead Schemas
# =====================================================

class LeadBase(BaseModel):
    """Base model untuk Lead"""
    customer_name: str
    customer_phone: str
    need: Optional[str] = None
    status: str = "baru"


class LeadCreate(LeadBase):
    """Request untuk create lead"""
    pass


class LeadUpdate(BaseModel):
    """Request untuk update lead"""
    status: Optional[str] = None
    need: Optional[str] = None


class LeadResponse(LeadBase):
    """Response untuk lead"""
    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# Test Chat Schemas
# =====================================================

class TestChatRequest(BaseModel):
    """Request untuk test chat endpoint"""
    message: str = Field(..., min_length=1, max_length=4096)


class TestChatResponse(BaseModel):
    """Response untuk test chat endpoint"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


# =====================================================
# Error Response Schema
# =====================================================

class ErrorResponse(BaseModel):
    """Response untuk error"""
    error: str
    detail: Optional[str] = None
