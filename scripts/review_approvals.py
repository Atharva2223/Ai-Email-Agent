from app.services.approval_service import list_pending_approvals, update_approval_status


def main():
    approvals = list_pending_approvals()

    if not approvals:
        print("No pending approvals.")
        return

    for item in approvals:
        print("\nApproval ID:", item["approval_id"])
        print("To:", item["to_email"])
        print("Proposed Action:", item["proposed_action"])
        print("Purpose:", item["proposed_purpose"])
        print("Draft Message:", item["proposed_message"])

        choice = input("Approve? (y/n): ").strip().lower()

        if choice == "y":
            update_approval_status(item["approval_id"], "approved")
            print("Approved.")
        else:
            update_approval_status(item["approval_id"], "rejected")
            print("Rejected.")


if __name__ == "__main__":
    main()