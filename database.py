"""
Database configuration dan management dengan SQLAlchemy dan Alembic
Mendukung SQLite (dev) dan PostgreSQL (production)
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from models import Base

# Create engine dengan dialect-specific options
if settings.database_url.startswith("sqlite"):
    # SQLite: gunakan StaticPool untuk threading
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    # Enable foreign keys di SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL atau database lainnya
    engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency untuk mendapatkan database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Buat semua tabel di database (fallback jika Alembic belum di-setup)"""
    Base.metadata.create_all(bind=engine)


class DatabaseService:
    """Service untuk operasi database umum"""

    # =====================================================
    # Business Management
    # =====================================================

    @staticmethod
    def get_or_create_business(db: Session, whatsapp_number: str, name: str = None):
        """Dapatkan atau buat bisnis baru dari nomor WhatsApp"""
        from models import Business

        business = db.query(Business).filter(
            Business.whatsapp_number == whatsapp_number
        ).first()

        if not business and name:
            business = Business(
                name=name,
                whatsapp_number=whatsapp_number,
                is_active=True
            )
            db.add(business)
            db.commit()
            db.refresh(business)

        return business

    @staticmethod
    def get_business_by_id(db: Session, business_id: int):
        """Dapatkan bisnis berdasarkan ID"""
        from models import Business
        return db.query(Business).filter(Business.id == business_id).first()

    @staticmethod
    def get_business_by_whatsapp(db: Session, whatsapp_number: str):
        """Dapatkan bisnis berdasarkan nomor WhatsApp"""
        from models import Business
        return db.query(Business).filter(
            Business.whatsapp_number == whatsapp_number,
            Business.is_active == True
        ).first()

    # =====================================================
    # Conversation Management
    # =====================================================

    @staticmethod
    def get_or_create_conversation(db: Session, business_id: int, customer_phone: str, customer_name: str = None):
        """Dapatkan atau buat percakapan baru"""
        from models import Conversation

        conversation = db.query(Conversation).filter(
            Conversation.business_id == business_id,
            Conversation.customer_phone == customer_phone
        ).first()

        if not conversation:
            conversation = Conversation(
                business_id=business_id,
                customer_phone=customer_phone,
                customer_name=customer_name,
                handoff=False
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        else:
            # Update customer_name jika berbeda
            if customer_name and not conversation.customer_name:
                conversation.customer_name = customer_name
                db.commit()
                db.refresh(conversation)

        return conversation

    @staticmethod
    def get_conversation_by_id(db: Session, conversation_id: int):
        """Dapatkan percakapan berdasarkan ID"""
        from models import Conversation
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def set_handoff(db: Session, conversation_id: int, handoff: bool):
        """Set status handoff untuk percakapan"""
        from models import Conversation

        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if conversation:
            conversation.handoff = handoff
            db.commit()
            db.refresh(conversation)

        return conversation

    # =====================================================
    # Chat Message Management
    # =====================================================

    @staticmethod
    def save_chat_message(db: Session, conversation_id: int, role: str, message: str):
        """Simpan pesan ke percakapan"""
        from models import ChatMessage

        chat_msg = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            message=message
        )
        db.add(chat_msg)
        db.commit()
        db.refresh(chat_msg)
        return chat_msg

    @staticmethod
    def get_recent_chat_history(db: Session, conversation_id: int, limit: int = 10):
        """Dapatkan riwayat percakapan terbaru sebagai list of dicts dengan role dan message"""
        from models import ChatMessage

        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

        # Convert ke format untuk LLM: [{"role": "user", "content": "..."}, ...]
        return [
            {"role": msg.role, "content": msg.message}
            for msg in messages
        ]

    # =====================================================
    # FAQ Management
    # =====================================================

    @staticmethod
    def get_faqs_for_business(db: Session, business_id: int):
        """Dapatkan semua FAQ untuk bisnis"""
        from models import FAQ

        return (
            db.query(FAQ)
            .filter(FAQ.business_id == business_id)
            .order_by(FAQ.order, FAQ.id)
            .all()
        )

    # =====================================================
    # Lead Management
    # =====================================================

    @staticmethod
    def create_lead(db: Session, business_id: int, customer_name: str, customer_phone: str, need: str = None):
        """Buat lead baru dari percakapan"""
        from models import Lead

        lead = Lead(
            business_id=business_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            need=need,
            status="baru"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def get_leads_for_business(db: Session, business_id: int, status: str = None):
        """Dapatkan leads untuk bisnis, dengan filter status optional"""
        from models import Lead

        query = db.query(Lead).filter(Lead.business_id == business_id)
        if status:
            query = query.filter(Lead.status == status)

        return query.order_by(Lead.created_at.desc()).all()

    # =====================================================
    # Legacy Support (untuk backward compatibility sementara)
    # =====================================================

    @staticmethod
    def get_or_create_user(db: Session, phone_number: str, name: str = None):
        """Legacy: Dapatkan atau buat user (untuk kompatibilitas)"""
        from models import User

        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            user = User(phone_number=phone_number, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def save_chat_message_legacy(db: Session, phone_number: str, role: str, message: str):
        """Legacy: Simpan pesan ke chat history (untuk kompatibilitas)"""
        from models import ChatHistory

        chat = ChatHistory(phone_number=phone_number, role=role, message=message)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    @staticmethod
    def get_recent_chat_history_legacy(db: Session, phone_number: str, limit: int = 10):
        """Legacy: Dapatkan riwayat chat per nomor (untuk kompatibilitas)"""
        from models import ChatHistory

        return (
            db.query(ChatHistory)
            .filter(ChatHistory.phone_number == phone_number)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()[::-1]  # Reverse untuk urutan ascending
        )

    @staticmethod
    def update_user_name(db: Session, phone_number: str, name: str):
        """Legacy: Update nama pengguna"""
        from models import User

        user = db.query(User).filter(User.phone_number == phone_number).first()
        if user:
            user.name = name
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_custom_response(db: Session, phone_number: str):
        """Legacy: Dapatkan custom response"""
        from models import CustomResponse

        return db.query(CustomResponse).filter(
            CustomResponse.phone_number == phone_number
        ).first()

    @staticmethod
    def save_or_update_custom_response(db: Session, phone_number: str, message: str):
        """Legacy: Simpan atau update custom response"""
        from models import CustomResponse

        existing = db.query(CustomResponse).filter(
            CustomResponse.phone_number == phone_number
        ).first()

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
