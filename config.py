from pydantic_settings import BaseSettings
from typing import Literal
from pydantic import Field


class Settings(BaseSettings):
    """Konfigurasi aplikasi dari environment variables"""

    # =====================================================
    # Gemini Configuration
    # =====================================================
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(..., env="GEMINI_MODEL")

    # =====================================================
    # WhatsApp Configuration
    # =====================================================
    wa_phone_number_id: str = Field(..., env="WA_PHONE_NUMBER_ID")
    wa_access_token: str = Field(..., env="WA_ACCESS_TOKEN")
    wa_verify_token: str = Field(..., env="WA_VERIFY_TOKEN")
    wa_api_version: str = Field("18", env="WA_API_VERSION")

    # =====================================================
    # Database Configuration
    # =====================================================
    database_url: str = Field(..., env="DATABASE_URL")

    # =====================================================
    # JWT & Security
    # =====================================================
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")

    # =====================================================
    # CORS & Frontend
    # =====================================================
    frontend_origin: str = Field("http://localhost:3000", env="FRONTEND_ORIGIN")

    # =====================================================
    # App Configuration
    # =====================================================
    port: int = Field(8000, env="PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    environment: Literal["development", "production"] = Field("development", env="ENVIRONMENT")
    app_name: str = "Gemini WhatsApp Bot (Multi-Client)"

    # =====================================================
    # Rate Limiting
    # =====================================================
    rate_limit_per_minute: int = Field(20, env="RATE_LIMIT_PER_MINUTE")
    max_message_length: int = Field(4096, env="MAX_MESSAGE_LENGTH")

    class Config:
        extra = "allow"
        env_file = ".env"
        case_sensitive = False

    @staticmethod
    def _validate_log_level(level: str) -> str:
        level = level.upper()
        valid = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        return level if level in valid else "INFO"

    @property
    def normalized_log_level(self) -> str:
        return self._validate_log_level(self.log_level)


# Inisialisasi settings
settings = Settings()
