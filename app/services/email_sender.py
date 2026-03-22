import smtplib
from email.mime.text import MIMEText
from app.core.config import EMAIL_ADDRESS, EMAIL_PASSWORD


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Send an email using Gmail SMTP.
    """
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError("Missing EMAIL_ADDRESS or EMAIL_PASSWORD in .env file.")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    print("\nEmail sent successfully.")