from app.core.config import validate_config
from app.services.email_generator import generate_email, generate_subject
from app.services.email_sender import send_email


def get_purpose_from_event(event: str) -> str:
    """
    Convert a business event into an email purpose.
    """
    event_map = {
        "signup": "Welcome email for a new user who signed up",
        "inactive": "Re-engagement email for a user who has not used the platform recently",
        "follow_up": "Follow-up email after no response from the user",
    }

    if event not in event_map:
        raise ValueError(f"Unsupported event: {event}")

    return event_map[event]


def run_email_workflow(user_name: str, to_email: str, event: str) -> None:
    """
    Run the full workflow:
    1. Validate config
    2. Convert event into purpose
    3. Generate subject
    4. Generate email body
    5. Send email
    """
    validate_config()

    purpose = get_purpose_from_event(event)
    subject = generate_subject(purpose)
    body = generate_email(user_name, purpose)

    print("\nEvent:")
    print(event)

    print("\nGenerated subject:")
    print(subject)

    print("\nGenerated body:")
    print(body)

    send_email(to_email=to_email, subject=subject, body=body)