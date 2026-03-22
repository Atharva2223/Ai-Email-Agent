import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def validate_config() -> None:
    """Validate required environment variables."""
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY in .env file.")
    if not EMAIL_ADDRESS:
        raise ValueError("Missing EMAIL_ADDRESS in .env file.")
    if not EMAIL_PASSWORD:
        raise ValueError("Missing EMAIL_PASSWORD in .env file.")