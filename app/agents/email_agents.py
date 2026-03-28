from google import genai
from app.core.config import GEMINI_API_KEY
from app.services.email_generator import generate_email, generate_subject
from app.services.email_sender import send_email
from datetime import timedelta
from app.services.reasoning_service import analyze_email_step_by_step
from app.services.approval_service import create_approval_request
import json
import re
from app.services.calendar_service import (
    _parse_datetime,
    check_availability,
    create_meeting_event,
    extract_meeting_link,
)
from app.services.memory_service import (
    get_user_memory,
    update_user_memory,
    append_interaction,
)



def _get_client():
    return genai.Client(api_key=GEMINI_API_KEY)


def decide_email_action(input_text: str, user_memory: dict) -> str:
    client = _get_client()

    prompt = f"""
You are an autonomous email assistant.

You are responsible for handling incoming emails on behalf of the user.
You are communicating with the email sender directly, not with the developer or system operator.

Your job is to:
1. Understand the sender's intent from the email
2. Use stored memory if it is relevant
3. Choose the best action
4. If information is missing, ask the sender directly in a polite and professional way

User Input:
{input_text}

Stored Memory:
{user_memory}

Possible actions:
- "reply_email" -> use when the sender needs a normal reply
- "schedule_meeting" -> use when the sender clearly wants to schedule a meeting
- "send_email" -> use for proactive outbound emails
- "ignore" -> use only when no reply or action is needed
- "ask_user" -> use when required information is missing or unclear

Important rules:
- NEVER ask the developer what to do
- NEVER say things like "Would you like me to ask the sender?"
- ALWAYS act as if you are replying directly to the sender
- If details are missing, choose "ask_user"
- The "message" field must contain the exact clarification email text to send to the sender
- Be concise, professional, and business-appropriate
- Return ONLY valid JSON
- Do NOT include markdown
- Do NOT include backticks
- Do NOT include explanations outside JSON

Schema:
{{
  "action": "reply_email | schedule_meeting | send_email | ignore | ask_user",
  "reason": "brief explanation",
  "details": {{
    "purpose": "short purpose text",
    "date": "meeting date if available",
    "time": "meeting time if available",
    "duration_minutes": 30,
    "message": "full sender-facing clarification or reply message if needed"
  }}
}}
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )

    return response.text



def requires_approval(reasoning_result: dict) -> bool:
    risk = reasoning_result.get("risk_assessment", {})
    decision = reasoning_result.get("decision", {})

    if risk.get("is_sensitive", False):
        return True

    action = decision.get("action", "")
    purpose = decision.get("purpose", "").lower()
    message = decision.get("message", "").lower()

    sensitive_keywords = [
        "quotation",
        "quote",
        "pricing",
        "contract",
        "legal",
        "invoice",
        "payment",
        "discount",
        "delivery timeline",
        "commitment",
    ]

    if action in {"send_email", "reply_email"}:
        if any(keyword in purpose or keyword in message for keyword in sensitive_keywords):
            return True

    return False
def parse_ai_json(response_text: str) -> dict:
    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("No JSON found")
    except Exception:
        print("Failed to parse AI response:")
        print(response_text)
        return {
            "intent": "unknown",
            "facts": {},
            "risk_assessment": {
                "is_sensitive": True,
                "reason": "Invalid model output"
            },
            "decision": {
                "action": "needs_approval",
                "purpose": "Manual review required",
                "message": "Unable to safely process this email automatically.",
                "duration_minutes": 30
            }
        }
def run_agent(user_name: str, to_email: str, input_text: str):
    user_memory = get_user_memory(to_email)

    print("\nUSER MEMORY:")
    print(user_memory)

    raw_reasoning = analyze_email_step_by_step(input_text, user_memory)

    print("\nRAW REASONING RESPONSE:")
    print(raw_reasoning)

    
    reasoning_result = parse_ai_json(raw_reasoning)

    print("\nREASONING RESULT:")
    print(reasoning_result)

    decision = reasoning_result.get("decision", {})
    action = decision.get("action", "needs_approval")
    purpose = decision.get("purpose", "")
    message = decision.get("message", "")
    duration_raw = decision.get("duration_minutes") or 30

    try:
        duration_minutes = int(duration_raw)
    except Exception:
        duration_minutes = 30

    if requires_approval(reasoning_result):
        approval_id = create_approval_request(
            {
                "to_email": to_email,
                "input_text": input_text,
                "reasoning_result": reasoning_result,
                "proposed_action": action,
                "proposed_purpose": purpose,
                "proposed_message": message,
            }
        )

        print(f"Approval required. Request created with ID: {approval_id}")
        return

    if action == "ignore":
        print("Agent decided no action is needed.")
        return

    if action == "ask_user":
        clarification_message = message or "Could you please provide the missing details so I can proceed?"
        send_email(to_email, "Clarification Required", clarification_message)
        print("Clarification email sent.")
        return

    if action == "reply_email":
        subject = generate_subject(purpose or "Reply to email")
        body = message or generate_email(user_name, purpose or "Reply to email")
        send_email(to_email, subject, body)
        print("Reply email sent.")
        return

    if action == "schedule_meeting":
        meeting_date = reasoning_result.get("facts", {}).get("date", "")
        meeting_time = reasoning_result.get("facts", {}).get("time", "")

        if not meeting_date or not meeting_time:
            send_email(
                to_email,
                "Need meeting details",
                "Could you please confirm the preferred date and time for the meeting?"
            )
            print("Meeting clarification email sent.")
            return

        start_dt = _parse_datetime(meeting_date, meeting_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        is_free = check_availability(start_dt, end_dt)

        if not is_free:
            send_email(
                to_email,
                "Meeting time unavailable",
                f"I’m unavailable at {start_dt.strftime('%Y-%m-%d %I:%M %p')}. Please suggest another time."
            )
            print("Requested alternate meeting time.")
            return

        event = create_meeting_event(
            summary=purpose or "Meeting",
            start_dt=start_dt,
            end_dt=end_dt,
            attendee_email=to_email,
            description="Scheduled automatically by AI email agent.",
        )

        meeting_link = extract_meeting_link(event)

        body = (
            f"Hi,\n\n"
            f"Your meeting has been scheduled.\n\n"
            f"Date: {start_dt.strftime('%Y-%m-%d')}\n"
            f"Time: {start_dt.strftime('%I:%M %p %Z')}\n"
            f"Duration: {duration_minutes} minutes\n"
            f"Meeting Link: {meeting_link}\n\n"
            f"Best regards,\n"
            f"AI Assistant"
        )

        send_email(to_email, "Meeting Confirmation", body)
        print("Meeting created and confirmation email sent.")
        return

    if action == "send_email":
        subject = generate_subject(purpose or "Outbound email")
        body = message or generate_email(user_name, purpose or "Outbound email")
        send_email(to_email, subject, body)
        print("Outbound email sent.")
        return

    approval_id = create_approval_request(
        {
            "to_email": to_email,
            "input_text": input_text,
            "reasoning_result": reasoning_result,
            "proposed_action": action,
            "proposed_purpose": purpose,
            "proposed_message": message,
        }
    )
    print(f"Fallback approval required. Request created with ID: {approval_id}")