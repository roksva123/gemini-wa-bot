import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import untuk setup testing
from main import app
from database import Base, get_db


# =====================================================
# Database Setup untuk Testing
# =====================================================

# Gunakan in-memory SQLite untuk testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override get_db dependency untuk testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# =====================================================
# Pytest Fixtures
# =====================================================

@pytest.fixture(scope="function")
def db():
    """Database session untuk setiap test"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client dengan database override"""
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """Event loop untuk async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_user_data():
    """Sample user data untuk testing"""
    return {
        "phone_number": "62812345678",
        "name": "Test User"
    }


@pytest.fixture
def sample_message_data():
    """Sample message data untuk testing"""
    return {
        "phone_number": "62812345678",
        "message": "Hello, this is a test message",
        "role": "user"
    }


# =====================================================
# Mock Data
# =====================================================

MOCK_WEBHOOK_MESSAGE = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "123456789",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "123456789",
                            "webhook_id": "123456789"
                        },
                        "contacts": [
                            {
                                "profile": {
                                    "name": "Test User"
                                },
                                "wa_id": "62812345678"
                            }
                        ],
                        "messages": [
                            {
                                "from": "62812345678",
                                "id": "wamid.123456789",
                                "timestamp": "1234567890",
                                "type": "text",
                                "text": {
                                    "body": "Hello bot!"
                                }
                            }
                        ]
                    },
                    "field": "messages"
                }
            ]
        }
    ]
}
