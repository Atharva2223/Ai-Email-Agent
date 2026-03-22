from app.workflows.email_workflow import run_email_workflow


def main() -> None:
    run_email_workflow(
        user_name="Atharva",
        to_email="atharva.patade@outlook.com",
        event="follow_up"
    )


if __name__ == "__main__":
    main()