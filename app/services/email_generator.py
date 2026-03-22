from google import genai
from app.core.config import GEMINI_API_KEY


def _get_client() -> genai.Client:
    """Create and return a Gemini client."""
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_subject(purpose: str) -> str:
    """
    Generate an email subject line based on the given purpose.
    """
    client = _get_client()

    prompt = f"""
    Write one professional email subject line.
    Purpose: {purpose}

    Rules:
    - Keep it under 8 words
    - Do not use quotes
    - Do not add multiple options
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text.strip()


def generate_email(user_name: str, purpose: str) -> str:
    """
    Generate a professional email body for the user.
    """
    client = _get_client()

    prompt = f"""
    Write a professional email for {user_name}.

    Purpose: {purpose}

    Rules:
    - Keep it under 150 words
    - Use a clear greeting
    - Use a polite and professional tone
    - End with a call to action
    - Output only the email body
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text.strip()