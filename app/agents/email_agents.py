from google import genai
from app.core.config import GEMINI_API_KEY
from app.services.email_generator import generate_email, generate_subject
from app.services.email_sender import send_email
import json
import re



def _get_client():
    return genai.Client(api_key=GEMINI_API_KEY)


def decide_email_action(event: str) -> dict:
    """
    AI decides what action to take based on event.
    Returns structured decision.
    """
    client = _get_client()

   
    prompt = f"""
You are an AI email assistant.

Based on the event below, decide:
1. Whether an email should be sent
2. The purpose of the email (if needed)

Event: {event}

Rules:
- If no email is needed, return:
  {{
    "send_email": false,
    "purpose": "none"
  }}

- If email is needed, return:
  {{
    "send_email": true,
    "purpose": "clear description of email purpose"
  }}

STRICT:
- Return ONLY valid JSON
- No explanation
- No markdown
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text


def parse_ai_decision(response_text: str) -> dict:
    

    try:
        # Extract JSON using regex
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_text = match.group(0)
            return json.loads(json_text)

        raise ValueError("No JSON found")

    except Exception:
        print("⚠️ Failed to parse AI response:")
        print(response_text)
        return {
            "send_email": False,
            "purpose": "Invalid response"
        }
def run_agent(user_name: str, to_email: str, event: str):
    raw_response = decide_email_action(event)

    print("\n🔍 RAW AI RESPONSE:")
    print(raw_response)

    decision = parse_ai_decision(raw_response)

    print("\nAI Decision:", decision)

    send_flag = decision.get("send_email", False)
    purpose = decision.get("purpose", "").strip()

    # 🚫 Case 1: AI says do NOT send
    if not send_flag:
        print("Agent decision: No email needed.")
        return

    # 🚫 Case 2: Invalid purpose
    if not purpose or purpose.lower() in ["n/a", "none", "no email"]:
        print("Invalid purpose returned by AI. Skipping email.")
        return

    # ✅ Normal flow
    subject = generate_subject(purpose)
    body = generate_email(user_name, purpose)

    send_email(to_email, subject, body)