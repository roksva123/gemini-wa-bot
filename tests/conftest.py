"""
Pytest configuration dan shared fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, Business, FAQ, AdminUser
from database import get_db
from routers.admin import hash_password


# Test database configuration
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"  # Use in-memory SQLite for tests


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """Create test session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db(TestingSessionLocal):
    """Get test database session"""
    connection = TestingSessionLocal.kw['bind'].connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_business(db):
    """Create sample business for testing"""
    business = Business(
        name="Test Coffee Shop",
        category="Kafe",
        tone="ramah",
        opening_hours="08:00 - 17:00",
        address="Jl. Test No. 123",
        order_flow="Pesan via WA, konfirmasi dalam 1 jam",
        whatsapp_number="628123456789",
        is_active=True
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@pytest.fixture
def sample_faqs(db, sample_business):
    """Create sample FAQs for testing"""
    faqs = [
        FAQ(
            business_id=sample_business.id,
            question="Apa saja menu kopi?",
            answer="Espresso, Americano, Cappuccino, Latte",
            order=1
        ),
        FAQ(
            business_id=sample_business.id,
            question="Berapa harganya?",
            answer="Mulai dari Rp 15.000",
            order=2
        ),
        FAQ(
            business_id=sample_business.id,
            question="Apakah bisa delivery?",
            answer="Bisa untuk area tertentu",
            order=3
        ),
    ]
    db.add_all(faqs)
    db.commit()
    return faqs


@pytest.fixture
def sample_admin_user(db, sample_business):
    """Create sample admin user for testing"""
    admin_user = AdminUser(
        business_id=sample_business.id,
        email="admin@testcoffee.com",
        password_hash=hash_password("secure_password_123"),
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user


@pytest.fixture
def admin_token(sample_admin_user):
    """Generate JWT token for sample admin user"""
    from routers.admin import create_access_token

    token = create_access_token(
        business_id=sample_admin_user.business_id,
        admin_user_id=sample_admin_user.id
    )
    return token


@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers with valid token"""
    return {"Authorization": f"Bearer {admin_token}"}
