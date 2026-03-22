from google import genai
from app.core.config import GEMINI_API_KEY
from app.services.email_generator import generate_email, generate_subject
from app.services.email_sender import send_email
from datetime import timedelta
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
import json
import re


def _get_client():
    return genai.Client(api_key=GEMINI_API_KEY)


def decide_email_action(input_text: str, user_memory: dict) -> str:
    client = _get_client()

    prompt = f"""
You are an intelligent email assistant.

Use the current user input and stored memory to decide the best action.

User Input:
{input_text}

Stored Memory:
{user_memory}

Possible actions:
- "reply_email"
- "schedule_meeting"
- "send_email"
- "ignore"
- "ask_user"

Return ONLY valid JSON.

Schema:
{{
  "action": "reply_email | schedule_meeting | send_email | ignore | ask_user",
  "reason": "brief explanation",
  "details": {{
    "purpose": "short purpose text",
    "date": "meeting date if available",
    "time": "meeting time if available",
    "duration_minutes": 30,
    "message": "clarification question if needed"
  }}
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text

def parse_ai_decision(response_text: str) -> dict:
    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("No JSON found")
    except Exception:
        print("Failed to parse AI response:")
        print(response_text)
        return {
            "action": "ask_user",
            "reason": "Invalid model output",
            "details": {
                "purpose": "",
                "date": "",
                "time": "",
                "duration_minutes": 30,
                "message": "Could you clarify the meeting date and time?",
            },
        }



def run_agent(user_name: str, to_email: str, input_text: str):
    user_memory = get_user_memory(to_email)

    print("\nUSER MEMORY:")
    print(user_memory)

    raw_response = decide_email_action(input_text, user_memory)

    print("\nRAW AI RESPONSE:")
    print(raw_response)

    decision = parse_ai_decision(raw_response)

    print("\nAI Decision:")
    print(decision)

    action = decision.get("action", "ask_user")
    details = decision.get("details", {})

    print(f"\nChosen action: {action}")
    print(f"Details: {details}")
    

    if action == "ignore":
        print("Agent decided no action is needed.")
        return

    if action == "ask_user":
        clarification_message = details.get(
            "message",
            "Could you clarify what you would like me to do?",
        )
        subject = "Need clarification"
        send_email(to_email, subject, clarification_message)
        print("Clarification email sent.")
        update_user_memory(
            to_email,
            {
                "last_action": "ask_user",
            },
        )

        append_interaction(
            to_email,
            {
                "input": input_text,
                "action": "ask_user",
                "details": details,
            },
        )
        return

    if action == "reply_email":
        purpose = details.get("purpose", "Reply to user email")
        subject = generate_subject(purpose)
        body = generate_email(user_name, purpose)
        send_email(to_email, subject, body)
        print("Reply email sent.")
        update_user_memory(
            to_email,
            {
                "last_action": "reply_email",
                "last_topic": details.get("purpose", "Reply to user email"),
            },
        )

        append_interaction(
            to_email,
            {
                "input": input_text,
                "action": "reply_email",
                "details": details,
            },
        )
        return

    if action == "send_email":
        purpose = details.get("purpose", "General outbound email")
        subject = generate_subject(purpose)
        body = generate_email(user_name, purpose)
        send_email(to_email, subject, body)
        print("Outbound email sent.")
        update_user_memory(
            to_email,
            {
                "last_action": "send_email",
                "last_topic": details.get("purpose", "General outbound email"),
            },
        )

        append_interaction(
            to_email,
            {
                "input": input_text,
                "action": "send_email",
                "details": details,
            },
        )
        return

    if action == "schedule_meeting":
        meeting_date = details.get("date", "").strip()
        meeting_time = details.get("time", "").strip()
        duration_raw = details.get("duration_minutes")
        if duration_raw is None:
            duration_minutes = 30
        else:
            try:
                duration_minutes = int(duration_raw)
            except Exception:
                duration_minutes = 30

        if not meeting_date or not meeting_time:
            clarification = (
                "I can set up the meeting, but I need both a date and time."
            )
            send_email(to_email, "Need meeting details", clarification)
            print("Asked user for missing meeting details.")
            return

        start_dt = _parse_datetime(meeting_date, meeting_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        is_free = check_availability(start_dt, end_dt)

        if not is_free:
            alternate_message = (
                f"I’m unavailable at {start_dt.strftime('%Y-%m-%d %I:%M %p')}. "
                "Please suggest another time."
            )
            send_email(to_email, "Meeting time unavailable", alternate_message)
            print("Requested alternate meeting time.")
            return

        event = create_meeting_event(
            summary="Meeting with user",
            start_dt=start_dt,
            end_dt=end_dt,
            attendee_email=to_email,
            description="Scheduled automatically by AI email agent.",
        )

        meeting_link = extract_meeting_link(event)

        subject = "Meeting Confirmation"
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

        send_email(to_email, subject, body)
        print("Meeting created and confirmation email sent.")
        update_user_memory(
            to_email,
            {
                "last_action": "schedule_meeting",
                "last_topic": details.get("purpose", "Meeting"),
                "last_meeting_date": start_dt.strftime("%Y-%m-%d"),
                "last_meeting_time": start_dt.strftime("%I:%M %p"),
                "preferred_meeting_time": start_dt.strftime("%I:%M %p"),
            },
        )

        append_interaction(
            to_email,
            {
                "input": input_text,
                "action": "schedule_meeting",
                "details": details,
                "meeting_link": meeting_link,
            },
        ) 
        update_user_memory(
            to_email,
            {
                "last_action": "schedule_meeting",
                "last_topic": details.get("purpose", "Meeting"),
                "last_meeting_date": start_dt.strftime("%Y-%m-%d"),
                "last_meeting_time": start_dt.strftime("%I:%M %p"),
                "preferred_meeting_time": start_dt.strftime("%I:%M %p"),
            },
        )

        append_interaction(
            to_email,
            {
                "input": input_text,
                "action": "schedule_meeting",
                "details": details,
                "meeting_link": meeting_link,
            },
        )
        return

    print("Unknown action received from agent.")