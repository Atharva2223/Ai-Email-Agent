import time

from app.agents.email_agents import run_agent
from app.services.gmail_service import (
    get_message,
    list_unread_messages,
    mark_as_read,
    parse_message,
)


POLL_INTERVAL_SECONDS = 60


def main() -> None:
    print("Inbox agent started...")

    while True:
        try:
            unread_messages = list_unread_messages(max_results=5)

            if not unread_messages:
                print("No unread emails found.")
            else:
                print(f"Found {len(unread_messages)} unread email(s).")

            for item in unread_messages:
                message_id = item["id"]
                raw_message = get_message(message_id)
                parsed = parse_message(raw_message)

                sender = parsed["from"]
                subject = parsed["subject"]
                body = parsed["body"]
                thread_id = parsed["thread_id"]

                print("\nProcessing email:")
                print("From:", sender)
                print("Subject:", subject)

                agent_input = f"""
From: {sender}
Subject: {subject}
Body:
{body}
"""

                run_agent(
                    user_name="Atharva",
                    to_email=sender,
                    input_text=agent_input,
                )

                mark_as_read(message_id)

            time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("Inbox agent stopped.")
            break
        except Exception as exc:
            print("Error while processing inbox:", exc)
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()