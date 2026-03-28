from google import genai
from app.core.config import GEMINI_API_KEY


def _get_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_subject(purpose: str) -> str:
    """
    Generate a concise professional email subject.
    """
    client = _get_client()

    prompt = f"""
    Write one professional email subject line.

    Purpose:
    {purpose}

    Rules:
    - Maximum 8 words
    - No quotation marks
    - No emojis
    - Only one subject line
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text.strip()


def generate_email(user_name: str, purpose: str) -> str:
    """
    Generate a professional email body.
    """
    client = _get_client()
    prompt = f"""
    Write a professional email for {user_name}.

    Purpose:
    {purpose}

    Requirements:
    - Use a proper greeting
    - Use short paragraphs
    - Leave a blank line between paragraphs
    - If needed, use bullet points
    - Include a professional closing
    - Do NOT write everything in one paragraph
    - Keep the tone clear, polite, and professional
    - Output only the email body
    """

    

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text.strip()