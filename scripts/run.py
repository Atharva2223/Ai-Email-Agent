from app.agents.email_agents import run_agent


def main():
    run_agent(
        email_context = f"""
        From: {sender}
        Subject: {subject}
        Body:
        {body}
        """
    )


if __name__ == "__main__":
    main()