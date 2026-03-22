from google import genai
from app.core.config import GEMINI_API_KEY
from app.services.email_generator import generate_email, generate_subject
from app.services.email_sender import send_email
import json
import re



def _get_client():
    return genai.Client(api_key=GEMINI_API_KEY)


def decide_email_action(event: str) -> str:
    client = _get_client()

    prompt = f"""
You are an intelligent email assistant.

Your job is to:
1. Understand the user input
2. Identify intent
3. Choose the correct action
4. Extract required details

User Input:
{event}

Available actions:
- "reply_email"
- "schedule_meeting"
- "send_email"
- "ignore"
- "ask_user"

Return ONLY valid JSON:

{{
    "action": "...",
    "reason": "...",
    "details": {{
        "purpose": "...",
        "time": "...",
        "date": "...",
        "message": "..."
    }}
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text

def parse_ai_decision(response_text: str) -> dict:
    import re
    import json

    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("No JSON found")

    except Exception:
        print("Failed to parse AI response:")
        print(response_text)
        return {
            "tool": "skip",
            "purpose": "none"
        }


def run_agent(user_name: str, to_email: str, input_text: str):
    raw_response = decide_email_action(input_text)

    print("\n🔍 RAW AI RESPONSE:")
    print(raw_response)

    decision = parse_ai_decision(raw_response)

    print("\nAI Decision:", decision)

    action = decision.get("action", "ignore")
    details = decision.get("details", {})

    print(f"\n🧠 Action: {action}")

    # 🧰 ACTION: IGNORE
    if action == "ignore":
        print("Agent decided to ignore.")
        return

    # 🧰 ACTION: REPLY EMAIL
    if action == "reply_email":
        purpose = details.get("purpose", "Reply to user")

        subject = generate_subject(purpose)
        body = generate_email(user_name, purpose)

        send_email(to_email, subject, body)
        return

    # 🧰 ACTION: SCHEDULE MEETING
    if action == "schedule_meeting":
        time = details.get("time", "Not specified")
        date = details.get("date", "Not specified")

        print(f"📅 Scheduling meeting on {date} at {time}")

        # 🔗 Step 1: Generate meeting link (mock)
        meeting_link = "https://meet.google.com/xyz-abc-def"

        # ✉️ Step 2: Create purpose for email
        purpose = f"Meeting scheduled on {date} at {time}. Include meeting link."

        # 🧠 Step 3: Generate email
        subject = generate_subject("Meeting Confirmation")
    
        body = f"""
        Hi,

        Your meeting has been scheduled.

        📅 Date: {date}
        ⏰ Time: {time}

        🔗 Meeting Link:
        {meeting_link}

        Please join using the link above.

        Best regards,
        AI Assistant
        """

        # 📤 Step 4: Send email
        send_email(to_email, subject, body)

        print("✅ Meeting email sent!")
        return
    

    # 🧰 ACTION: SEND EMAIL
    if action == "send_email":
        purpose = details.get("purpose", "General email")

        subject = generate_subject(purpose)
        body = generate_email(user_name, purpose)

        send_email(to_email, subject, body)
        return

    # 🧰 ACTION: ASK USER
    if action == "ask_user":
        print("Agent needs more info:", details.get("message"))
        return

    print("⚠️ Unknown action")