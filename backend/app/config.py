"""
===========================================================
Config
-----------------------------------------------------------
Central place for all environment-driven settings.
Every service/agent imports `settings` from here instead of
calling os.getenv() directly all over the codebase.
===========================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")
    # Groq's API is OpenAI-SDK compatible - this is the only line that
    # differs between "using OpenAI" and "using Groq for free".
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ordeasy.db")

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    LOW_CONFIDENCE_THRESHOLD: float = 0.80

    # Email ingestion (IMAP) - for the continuous inbox-polling pipeline
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "imap.gmail.com")
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASS: str = os.getenv("EMAIL_PASS", "")
    EMAIL_FOLDER: str = os.getenv("EMAIL_FOLDER", "INBOX")
    EMAIL_POLL_MINUTES: int = int(os.getenv("EMAIL_POLL_MINUTES", "5"))
    ENABLE_EMAIL_POLLING: bool = os.getenv("ENABLE_EMAIL_POLLING", "false").lower() == "true"


settings = Settings()
