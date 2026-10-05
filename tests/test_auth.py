"""
Tests untuk routers/admin.py - Authentication dan JWT
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from jose import jwt

from main import app
from database import Base, get_db
from models import Business, AdminUser
from config import settings
from routers.admin import hash_password, verify_password, create_access_token, verify_token
from schemas import TokenData


# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
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
client = TestClient(app)


class TestPasswordHashing:
    """Test password hashing dan verification"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "my_secure_password"
        hashed = hash_password(password)

        # Hash should be different from original
        assert hashed != password
        # Hash should be string
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """Test verify correct password"""
        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify incorrect password"""
        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_hash_same_password_different_results(self):
        """Test bahwa hashing password yang sama menghasilkan hash berbeda"""
        password = "my_secure_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (bcrypt adds salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """Test JWT token generation dan verification"""

    def test_create_access_token(self):
        """Test token creation"""
        business_id = 1
        admin_user_id = 1

        token = create_access_token(business_id, admin_user_id)

        # Token should be string
        assert isinstance(token, str)
        # Token should have 3 parts (header.payload.signature)
        assert token.count('.') == 2

    def test_token_contains_correct_data(self):
        """Test token contains correct data"""
        business_id = 123
        admin_user_id = 456

        token = create_access_token(business_id, admin_user_id)

        # Decode token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        assert payload['business_id'] == business_id
        assert payload['admin_user_id'] == admin_user_id
        assert 'exp' in payload

    def test_token_expiration(self):
        """Test token contains expiration"""
        business_id = 1
        admin_user_id = 1

        token = create_access_token(business_id, admin_user_id)
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        # Expiration should be in future
        exp_time = datetime.utcfromtimestamp(payload['exp'])
        now = datetime.utcnow()

        assert exp_time > now
        # Should be approximately jwt_expiration_hours from now
        diff = (exp_time - now).total_seconds() / 3600
        assert 23 < diff < 25  # Allow 1 hour margin


class TestLoginEndpoint:
    """Test POST /api/auth/login endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database dengan admin user"""
        db = TestingSessionLocal()

        # Create business
        business = Business(
            name="Test Business",
            whatsapp_number="628123456789",
            tone="ramah",
            is_active=True
        )
        db.add(business)
        db.commit()
        db.refresh(business)

        # Create admin user
        admin_user = AdminUser(
            business_id=business.id,
            email="admin@test.com",
            password_hash=hash_password("test_password_123"),
            is_active=True
        )
        db.add(admin_user)
        db.commit()

        yield

        # Cleanup
        db.query(AdminUser).delete()
        db.query(Business).delete()
        db.commit()
        db.close()

    def test_login_success(self):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.com",
                "password": "test_password_123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["business_id"] == 1

    def test_login_wrong_password(self):
        """Test login dengan password salah"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.com",
                "password": "wrong_password"
            }
        )

        assert response.status_code == 401
        assert "Email atau password salah" in response.json()["detail"]

    def test_login_user_not_found(self):
        """Test login dengan email yang tidak terdaftar"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "notfound@test.com",
                "password": "test_password_123"
            }
        )

        assert response.status_code == 401
        assert "Email atau password salah" in response.json()["detail"]

    def test_login_inactive_user(self):
        """Test login dengan user yang tidak aktif"""
        db = TestingSessionLocal()

        # Set user as inactive
        admin_user = db.query(AdminUser).filter(
            AdminUser.email == "admin@test.com"
        ).first()
        admin_user.is_active = False
        db.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.com",
                "password": "test_password_123"
            }
        )

        assert response.status_code == 403
        assert "tidak aktif" in response.json()["detail"]

        db.close()


class TestProtectedEndpoints:
    """Test protected endpoints require valid JWT"""

    @pytest.fixture
    def valid_token(self):
        """Generate valid token"""
        return create_access_token(business_id=1, admin_user_id=1)

    def test_get_business_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/business")
        assert response.status_code == 403

    def test_get_business_with_invalid_token(self):
        """Test accessing protected endpoint dengan invalid token"""
        response = client.get(
            "/api/business",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 403

    def test_get_faqs_without_token(self):
        """Test accessing /faqs without token"""
        response = client.get("/api/faqs")
        assert response.status_code == 403

    def test_get_conversations_without_token(self):
        """Test accessing /conversations without token"""
        response = client.get("/api/conversations")
        assert response.status_code == 403


class TestHealthEndpoint:
    """Test public health endpoint"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
