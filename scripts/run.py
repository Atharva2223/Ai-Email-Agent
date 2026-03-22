from app.workflows.email_workflow import run_email_workflow


def main() -> None:
    run_email_workflow(
        user_name="Atharva",
        to_email="test@example.com",
        purpose="Welcome email for a new user who signed up for our platform",
    )


if __name__ == "__main__":
    main()