from app.core.config import validate_config
from app.services.email_generator import generate_email, generate_subject
from app.services.email_sender import send_email


def run_email_workflow(user_name: str, to_email: str, purpose: str) -> None:
    """
    Run the full email workflow:
    1. Validate config
    2. Generate subject
    3. Generate body
    4. Preview/send email
    """
    validate_config()

    subject = generate_subject(purpose)
    body = generate_email(user_name, purpose)

    print("Generated subject:")
    print(subject)
    print("\nGenerated body:")
    print(body)

    send_email(to_email=to_email, subject=subject, body=body)