"""
Multi-client WhatsApp Bot Models
Supports multiple businesses with their own FAQs, conversations, and leads
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# =====================================================
# Business & Configuration Models
# =====================================================

class Business(Base):
    """Model untuk bisnis/toko yang menggunakan chatbot"""
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True)  # e.g., "Toko Kopi", "Klinik Kesehatan"
    tone = Column(String(50), nullable=False, default="ramah")  # ramah, formal, profesional, santai
    opening_hours = Column(Text, nullable=True)  # JSON string or free text
    address = Column(Text, nullable=True)
    order_flow = Column(Text, nullable=True)  # Cara memesan atau eskalasi ke admin
    whatsapp_number = Column(String(20), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    faqs = relationship("FAQ", back_populates="business", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="business", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="business", cascade="all, delete-orphan")
    admin_users = relationship("AdminUser", back_populates="business", cascade="all, delete-orphan")


class FAQ(Base):
    """Model untuk FAQ/katalog produk per bisnis"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    order = Column(Integer, default=0)  # Untuk urutan tampilan
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    business = relationship("Business", back_populates="faqs")


# =====================================================
# Conversation & Message Models
# =====================================================

class Conversation(Base):
    """Model untuk percakapan antara customer dan bot"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_name = Column(String(100), nullable=True)
    handoff = Column(Boolean, default=False)  # True = admin meng-handle, skip LLM
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    # Relationships
    business = relationship("Business", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Model untuk pesan dalam percakapan"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" atau "assistant"
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


# =====================================================
# Lead Model
# =====================================================

class Lead(Base):
    """Model untuk calon pelanggan yang tertarik (dari percakapan)"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=False, index=True)
    need = Column(Text, nullable=True)  # Apa yang mereka butuhkan
    status = Column(String(50), nullable=False, default="baru")  # baru, follow-up, selesai
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    business = relationship("Business", back_populates="leads")


# =====================================================
# Admin User Model
# =====================================================

class AdminUser(Base):
    """Model untuk admin/pemilik bisnis yang login ke dashboard"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    business = relationship("Business", back_populates="admin_users")


# =====================================================
# Legacy Models (untuk backward compatibility sementara)
# =====================================================

class User(Base):
    """Legacy: Model untuk menyimpan data pengguna WhatsApp (akan dihapus)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ChatHistory(Base):
    """Legacy: Model untuk menyimpan riwayat percakapan (akan dihapus)"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), ForeignKey("users.phone_number", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # 'user' atau 'model'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class CustomResponse(Base):
    """Legacy: Model untuk custom response per nomor (akan dihapus)"""
    __tablename__ = "custom_responses"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
