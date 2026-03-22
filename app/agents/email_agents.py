from google import genai
from app.core.config import GEMINI_API_KEY
from app.services.email_generator import generate_email, generate_subject
from app.services.email_sender import send_email
import json
import re



def _get_client():
    return genai.Client(api_key=GEMINI_API_KEY)

def parse_ai_decision(response_text: str) -> dict:
    import re
    import json

    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("No JSON found")

    except Exception:
        print("⚠️ Failed to parse AI response:")
        print(response_text)
        return {
            "tool": "skip",
            "purpose": "none"
        }
def decide_email_action(event: str) -> str:
    client = _get_client()

    prompt = f"""
    You are an AI email automation agent.

    Based on the event below, decide:
    1. Which action (tool) to use
    2. The purpose (if needed)

    Available tools:
    - "generate_and_send_email"
    - "skip"

    Event: {event}

    Rules:
    - If email is needed → use "generate_and_send_email"
    - If no action needed → use "skip"

    Output ONLY valid JSON:
    {{
        "tool": "generate_and_send_email" or "skip",
        "purpose": "..."
    }}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text


def run_agent(user_name: str, to_email: str, event: str):
    raw_response = decide_email_action(event)

    print("\n🔍 RAW AI RESPONSE:")
    print(raw_response)

    decision = parse_ai_decision(raw_response)

    print("\nAI Decision:", decision)

    tool = decision.get("tool", "skip")
    purpose = decision.get("purpose", "").strip()

    # 🧰 TOOL: SKIP
    if tool == "skip":
        print("🛑 Agent chose to skip email.")
        return

    # 🧰 TOOL: GENERATE + SEND
    if tool == "generate_and_send_email":

        if not purpose or purpose.lower() in ["none", "n/a"]:
            print("⚠️ Invalid purpose. Skipping.")
            return

        subject = generate_subject(purpose)
        body = generate_email(user_name, purpose)

        send_email(to_email, subject, body)
        return

    # 🚫 Unknown tool
    print(f"⚠️ Unknown tool: {tool}")