from pydantic_settings import BaseSettings


from typing import Literal
from pydantic import Field

class Settings(BaseSettings):
    """Konfigurasi aplikasi dari environment variables"""

    # Gemini Configuration (required)
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(..., env="GEMINI_MODEL")

    # WhatsApp Configuration (required)
    wa_phone_number_id: str = Field(..., env="WA_PHONE_NUMBER_ID")
    wa_access_token: str = Field(..., env="WA_ACCESS_TOKEN")
    wa_verify_token: str = Field(..., env="WA_VERIFY_TOKEN")

    # Optional: API version for WhatsApp (default 18)
    wa_api_version: str = Field("18", env="WA_API_VERSION")

    # Database Configuration (required)
    database_url: str = Field(..., env="DATABASE_URL")

    # App Configuration
    port: int = Field(8000, env="PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    environment: Literal["development", "production"] = Field("development", env="ENVIRONMENT")
    app_name: str = "Gemini WhatsApp Bot"

    class Config:
        extra = "allow"
        env_file = ".env"
        case_sensitive = False

    # Validate log level on load
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
