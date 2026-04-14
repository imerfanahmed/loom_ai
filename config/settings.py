"""
Loom CLI — Configuration Settings
Loads environment variables and provides application-wide defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    """Centralised application settings."""

    # ── Gemini AI ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Default network device ────────────────────────────────────────────
    DEFAULT_DEVICE = {
        "hostname": "Router-1",
        "ip": "172.16.57.137",
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin1pass",
    }

    @property
    def has_api_key(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY != "your-api-key-here")


settings = Settings()
