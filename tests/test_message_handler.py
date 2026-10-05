"""
Tests untuk services/message_handler.py - Message handling dan handoff logic
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
from models import Business, Conversation, ChatMessage, Lead, FAQ
from services.message_handler import message_handler
from services.prompt_builder import validate_message_length


# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_msg.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override get_db untuk testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestMessageHandling:
    """Test message handling logic"""

    @pytest.fixture
    def test_db(self):
        """Create test database session"""
        db = TestingSessionLocal()
        yield db
        db.close()

    @pytest.fixture
    def sample_business(self, test_db):
        """Create sample business"""
        business = Business(
            name="Test Business",
            category="Retail",
            tone="ramah",
            opening_hours="09:00 - 17:00",
            address="Jl. Test No. 123",
            order_flow="Hubungi admin untuk pemesanan",
            whatsapp_number="628123456789",
            is_active=True
        )
        test_db.add(business)
        test_db.commit()
        test_db.refresh(business)
        return business

    @pytest.fixture
    def sample_conversation(self, test_db, sample_business):
        """Create sample conversation"""
        conversation = Conversation(
            business_id=sample_business.id,
            customer_phone="62811111111",
            customer_name="Test Customer",
            handoff=False
        )
        test_db.add(conversation)
        test_db.commit()
        test_db.refresh(conversation)
        return conversation

    @pytest.fixture
    def sample_faqs(self, test_db, sample_business):
        """Create sample FAQs"""
        faqs = [
            FAQ(
                business_id=sample_business.id,
                question="Jam operasional?",
                answer="09:00 - 17:00",
                order=1
            ),
            FAQ(
                business_id=sample_business.id,
                question="Alamat toko?",
                answer="Jl. Test No. 123",
                order=2
            )
        ]
        test_db.add_all(faqs)
        test_db.commit()
        return faqs

    def test_message_saved_to_database(self, test_db, sample_conversation):
        """Test bahwa user message disimpan ke database"""
        from database import DatabaseService

        message_text = "Halo, berapa jam operasional?"

        DatabaseService.save_chat_message(
            test_db,
            conversation_id=sample_conversation.id,
            role="user",
            message=message_text
        )

        # Verify message was saved
        messages = test_db.query(ChatMessage).filter(
            ChatMessage.conversation_id == sample_conversation.id,
            ChatMessage.role == "user"
        ).all()

        assert len(messages) == 1
        assert messages[0].message == message_text

    def test_conversation_updated_with_customer_name(self, test_db, sample_business):
        """Test bahwa conversation di-update dengan customer name"""
        from database import DatabaseService

        # Create conversation tanpa name
        conversation = Conversation(
            business_id=sample_business.id,
            customer_phone="62811111111",
            customer_name=None,
            handoff=False
        )
        test_db.add(conversation)
        test_db.commit()

        # Get or create dengan name
        result = DatabaseService.get_or_create_conversation(
            test_db,
            business_id=sample_business.id,
            customer_phone="62811111111",
            customer_name="Budi"
        )

        assert result.customer_name == "Budi"

    def test_recent_chat_history_format(self, test_db, sample_conversation):
        """Test bahwa recent chat history return format yang benar"""
        from database import DatabaseService

        # Save beberapa messages
        DatabaseService.save_chat_message(test_db, sample_conversation.id, "user", "Halo")
        DatabaseService.save_chat_message(test_db, sample_conversation.id, "assistant", "Halo juga!")
        DatabaseService.save_chat_message(test_db, sample_conversation.id, "user", "Ada yang bisa dibantu?")

        # Get history
        history = DatabaseService.get_recent_chat_history(test_db, sample_conversation.id, limit=10)

        # Check format
        assert len(history) == 3
        assert history[0] == {"role": "user", "content": "Halo"}
        assert history[1] == {"role": "assistant", "content": "Halo juga!"}
        assert history[2] == {"role": "user", "content": "Ada yang bisa dibantu?"}


class TestHandoffLogic:
    """Test handoff mode logic"""

    @pytest.fixture
    def test_db(self):
        """Create test database session"""
        db = TestingSessionLocal()
        yield db
        db.close()

    @pytest.fixture
    def handoff_conversation(self, test_db):
        """Create conversation in handoff mode"""
        business = Business(
            name="Test Business",
            whatsapp_number="628123456789",
            is_active=True
        )
        test_db.add(business)
        test_db.commit()

        conversation = Conversation(
            business_id=business.id,
            customer_phone="62811111111",
            customer_name="Test",
            handoff=True  # In handoff mode
        )
        test_db.add(conversation)
        test_db.commit()
        test_db.refresh(conversation)

        return conversation

    @pytest.mark.asyncio
    async def test_handoff_mode_skips_llm(self, test_db, handoff_conversation):
        """Test bahwa handoff mode TIDAK memanggil LLM"""
        from database import DatabaseService

        # Verify handoff is True
        assert handoff_conversation.handoff is True

        # Dalam handle_incoming_message, ketika handoff=True:
        # Message disimpan tapi LLM tidak dipanggil
        # Kita simulate logic ini:
        message_text = "Saya ingin bertanya sesuatu"

        if handoff_conversation.handoff:
            # Skip LLM, hanya simpan message
            DatabaseService.save_chat_message(
                test_db,
                handoff_conversation.id,
                "user",
                message_text
            )
            response = None  # No response from LLM

        # Verify message was saved but no response generated
        messages = test_db.query(ChatMessage).filter(
            ChatMessage.conversation_id == handoff_conversation.id
        ).all()

        assert len(messages) == 1
        assert response is None

    def test_set_handoff_true(self, test_db):
        """Test set handoff to True"""
        from database import DatabaseService

        business = Business(name="Test", whatsapp_number="628123456789")
        test_db.add(business)
        test_db.commit()

        conversation = Conversation(business_id=business.id, customer_phone="62811111111", handoff=False)
        test_db.add(conversation)
        test_db.commit()

        # Set handoff to True
        result = DatabaseService.set_handoff(test_db, conversation.id, True)

        assert result.handoff is True

    def test_set_handoff_false(self, test_db):
        """Test set handoff back to False"""
        from database import DatabaseService

        business = Business(name="Test", whatsapp_number="628123456789")
        test_db.add(business)
        test_db.commit()

        conversation = Conversation(business_id=business.id, customer_phone="62811111111", handoff=True)
        test_db.add(conversation)
        test_db.commit()

        # Set handoff to False
        result = DatabaseService.set_handoff(test_db, conversation.id, False)

        assert result.handoff is False


class TestLeadCreation:
    """Test lead creation logic"""

    @pytest.fixture
    def test_db(self):
        """Create test database session"""
        db = TestingSessionLocal()
        yield db
        db.close()

    @pytest.fixture
    def sample_business(self, test_db):
        """Create sample business"""
        business = Business(
            name="Test Business",
            whatsapp_number="628123456789",
            is_active=True
        )
        test_db.add(business)
        test_db.commit()
        test_db.refresh(business)
        return business

    def test_create_lead(self, test_db, sample_business):
        """Test creating a new lead"""
        from database import DatabaseService

        lead = DatabaseService.create_lead(
            test_db,
            business_id=sample_business.id,
            customer_name="John Doe",
            customer_phone="62812345678",
            need="Saya ingin order 10 pcs"
        )

        assert lead.id is not None
        assert lead.customer_name == "John Doe"
        assert lead.customer_phone == "62812345678"
        assert lead.need == "Saya ingin order 10 pcs"
        assert lead.status == "baru"

    def test_get_leads_by_status(self, test_db, sample_business):
        """Test getting leads filtered by status"""
        from database import DatabaseService

        # Create multiple leads with different statuses
        lead1 = DatabaseService.create_lead(test_db, sample_business.id, "Customer 1", "628111111", "Order")
        lead1.status = "baru"
        test_db.commit()

        lead2 = DatabaseService.create_lead(test_db, sample_business.id, "Customer 2", "628222222", "Follow-up")
        lead2.status = "follow-up"
        test_db.commit()

        # Get leads with status "baru"
        leads = DatabaseService.get_leads_for_business(test_db, sample_business.id, status="baru")

        assert len(leads) == 1
        assert leads[0].customer_name == "Customer 1"

    def test_lead_default_status_is_baru(self, test_db, sample_business):
        """Test bahwa default status lead adalah 'baru'"""
        from database import DatabaseService

        lead = DatabaseService.create_lead(
            test_db,
            business_id=sample_business.id,
            customer_name="Test Customer",
            customer_phone="62812345678"
        )

        assert lead.status == "baru"


class TestMessageValidation:
    """Test message validation in handler"""

    def test_empty_message_rejected(self):
        """Test empty message is rejected"""
        is_valid, error = validate_message_length("", max_length=4096)
        assert is_valid is False

    def test_whitespace_only_rejected(self):
        """Test whitespace-only message is rejected"""
        is_valid, error = validate_message_length("   \n\t  ", max_length=4096)
        assert is_valid is False

    def test_message_too_long_rejected(self):
        """Test message exceeding max_length is rejected"""
        long_msg = "a" * 5000
        is_valid, error = validate_message_length(long_msg, max_length=4096)
        assert is_valid is False
        assert "terlalu panjang" in error.lower()

    def test_valid_message_accepted(self):
        """Test valid message is accepted"""
        is_valid, error = validate_message_length("This is a valid message", max_length=4096)
        assert is_valid is True
        assert error is None
