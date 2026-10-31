"""Settings and environment configuration for Restful-Booker API tests."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Central settings configuration class."""

    LIVE_BASE_URL: str = "https://restful-booker.herokuapp.com"
    BASE_URL: str = os.getenv("BASE_URL", LIVE_BASE_URL).rstrip("/")

    AUTH_USERNAME: str = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD: str = os.getenv("AUTH_PASSWORD", "password123")

    DEFAULT_TIMEOUT: int = int(os.getenv("TIMEOUT", "15"))
    USE_MOCK: bool = os.getenv("USE_MOCK", "false").lower() in ("true", "1", "yes")

    MOCK_HOST: str = os.getenv("MOCK_HOST", "127.0.0.1")
    MOCK_PORT: int = int(os.getenv("MOCK_PORT", "8001"))

    @classmethod
    def get_base_url(cls, use_mock: bool = False) -> str:
        """Return base URL based on whether mock is enabled."""
        if use_mock or cls.USE_MOCK:
            return f"http://{cls.MOCK_HOST}:{cls.MOCK_PORT}"
        return cls.BASE_URL


settings = Settings()
