import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    IS_APP_SERVICE = bool(os.getenv("WEBSITE_SITE_NAME"))
    SECRET_KEY = os.getenv("SECRET_KEY") or "local-development-only-secret"
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "campus_express.db"))
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or "local-development-only-password"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_APP_SERVICE
    
    # Microsoft Foundry / Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    # Alternative direct OpenAI-compatible endpoint
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
    
    # AI Fallback Mode: 'auto' allows offline demonstrations without an Azure subscription
    AI_FALLBACK_MODE = os.getenv("AI_FALLBACK_MODE", "auto").lower()
    
    @classmethod
    def is_azure_configured(cls) -> bool:
        """Returns True if Azure OpenAI / Foundry credentials are provided."""
        return bool(cls.AZURE_OPENAI_API_KEY and cls.AZURE_OPENAI_ENDPOINT)
    
    @classmethod
    def is_openai_configured(cls) -> bool:
        """Returns True if standard OpenAI API key is provided."""
        return bool(cls.OPENAI_API_KEY)


if Config.IS_APP_SERVICE and (
    len(os.getenv("SECRET_KEY", "")) < 32
    or len(os.getenv("ADMIN_PASSWORD", "")) < 16
):
    raise RuntimeError(
        "App Service requires SECRET_KEY (32+ characters) and ADMIN_PASSWORD (16+ characters)."
    )
