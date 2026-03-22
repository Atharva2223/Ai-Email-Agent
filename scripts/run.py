from app.agents.email_agents import run_agent


def main():
    run_agent(
        user_name="Atharva",
        to_email="atharva.patade@outlook.com",
        event="user active daily"
    )


if __name__ == "__main__":
    main()