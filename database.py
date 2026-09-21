from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config import settings

# Create database engine
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk semua models
Base = declarative_base()


class User(Base):
    """Model untuk menyimpan data pengguna WhatsApp"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ChatHistory(Base):
    """Model untuk menyimpan riwayat percakapan"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), ForeignKey("users.phone_number", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # 'user' atau 'model'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class CustomResponse(Base):
    """Model untuk menyimpan custom response per nomor telepon"""
    __tablename__ = "custom_responses"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


def get_db():
    """Dependency untuk mendapatkan database session, dengan rollback pada error"""
    db = SessionLocal()
    try:
        yield db
        # Commit if everything went fine (FastAPI will commit in routes if needed)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Buat semua tabel di database"""
    Base.metadata.create_all(bind=engine)


class DatabaseService:
    """Service untuk operasi database"""

    @staticmethod
    def get_or_create_user(db: Session, phone_number: str, name: str = None) -> User:
        """Dapatkan atau buat user baru"""
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            user = User(phone_number=phone_number, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def save_chat_message(db: Session, phone_number: str, role: str, message: str) -> ChatHistory:
        """Simpan pesan ke chat history"""
        chat = ChatHistory(phone_number=phone_number, role=role, message=message)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    @staticmethod
    def get_recent_chat_history(db: Session, phone_number: str, limit: int = 10) -> list[ChatHistory]:
        """Dapatkan riwayat percakapan terbaru"""
        return (
            db.query(ChatHistory)
            .filter(ChatHistory.phone_number == phone_number)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()[::-1]  # Reverse untuk urutan ascending
        )

    @staticmethod
    def update_user_name(db: Session, phone_number: str, name: str) -> User:
        """Update nama pengguna"""
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if user:
            user.name = name
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_custom_response(db: Session, phone_number: str) -> CustomResponse:
        """Dapatkan custom response untuk nomor telepon tertentu"""
        return db.query(CustomResponse).filter(CustomResponse.phone_number == phone_number).first()

    @staticmethod
    def save_or_update_custom_response(db: Session, phone_number: str, message: str) -> CustomResponse:
        """Simpan atau update custom response"""
        existing = db.query(CustomResponse).filter(CustomResponse.phone_number == phone_number).first()

        if existing:
            existing.message = message
            db.commit()
            db.refresh(existing)
            return existing
        else:
            custom_response = CustomResponse(phone_number=phone_number, message=message)
            db.add(custom_response)
            db.commit()
            db.refresh(custom_response)
            return custom_response
