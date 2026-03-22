from app.agents.email_agents import run_agent


def main():
    run_agent(
        user_name="Atharva",
        to_email="atharva.patade@outlook.com",
        input_text = "Can we do the same time again next week?",
    )


if __name__ == "__main__":
    main()