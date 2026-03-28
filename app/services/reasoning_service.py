from google import genai
from app.core.config import GEMINI_API_KEY


def _get_client():
    return genai.Client(api_key=GEMINI_API_KEY)


def analyze_email_step_by_step(input_text: str, user_memory: dict) -> str:
    client = _get_client()

    prompt = f"""
You are an autonomous email assistant.

Analyze the incoming email in multiple reasoning steps.

Incoming Email:
{input_text}

Stored Memory:
{user_memory}

Think through these steps:
1. Identify the sender's intent
2. Extract important facts
3. Decide whether the email is sensitive, high-impact, or requires approval
4. Choose the best action

Sensitive/high-impact cases include:
- quotations or pricing commitments
- financial commitments
- legal or contractual communication
- external business commitments
- executive or high-priority communication
- uncertain replies where mistakes could matter

Return ONLY valid JSON.

Schema:
{{
  "intent": "short description",
  "facts": {{
    "topic": "main topic",
    "date": "",
    "time": "",
    "quantity": "",
    "urgency": "low | medium | high"
  }},
  "risk_assessment": {{
    "is_sensitive": true,
    "reason": "why it is sensitive or not"
  }},
  "decision": {{
    "action": "reply_email | schedule_meeting | send_email | ignore | ask_user | needs_approval",
    "purpose": "short purpose text",
    "message": "sender-facing draft or clarification email",
    "duration_minutes": 30
  }}
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text