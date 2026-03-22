from app.agents.email_agents import run_agent


def main():
    run_agent(
        user_name="Atharva",
        to_email="atharva.patade@outlook.com",
        input_text = "Can we schedule a meeting tomorrow at 3pm to discuss pricing for 30 minutes?",
    )


if __name__ == "__main__":
    main()