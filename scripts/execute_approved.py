from app.services.approval_service import load_approvals, save_approvals
from app.services.email_sender import send_email


def main():
    approvals = load_approvals()
    updated = False

    for item in approvals:
        if item.get("status") != "approved":
            continue

        if item.get("executed") is True:
            continue

        action = item.get("proposed_action")
        to_email = item.get("to_email")
        purpose = item.get("proposed_purpose", "Approved Action")
        message = item.get("proposed_message", "")

        if action in {"ask_user", "reply_email", "send_email"}:
            subject = purpose or "Approved Email"
            send_email(to_email, subject, message)
            item["executed"] = True
            updated = True
            print(f"Executed approval: {item['approval_id']}")

    if updated:
        save_approvals(approvals)
        print("Approved actions executed.")
    else:
        print("No approved actions pending execution.")


if __name__ == "__main__":
    main()