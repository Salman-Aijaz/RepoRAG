"""
▶️  Entry point — run this file to start the CLI chatbot
"""

import os
from dotenv import load_dotenv
from core.explainer import CodebaseExplainer

load_dotenv()


def main():
    print("\n🤖 Codebase Explainer AI (ENV + FREE MODE)\n")

    try:
        bot = CodebaseExplainer()
    except RuntimeError as e:
        print(e)
        return

    repo_url = input("Enter GitHub repository URL: ").strip()
    if not repo_url:
        print("❌ Repository URL required")
        return

    # Optional: pre-load token from .env (user can set GITHUB_TOKEN there)
    # If repo is private and no token in .env, repo_manager will ask at runtime
    github_token = os.getenv("GITHUB_TOKEN")

    bot.ingest_repository(repo_url, token=github_token)

    if not bot.qa_chain:
        return

    print("💬 Ask questions (type 'quit' to exit)\n")

    while True:
        q = input("You: ").strip()
        if not q:
            continue
        if q.lower() in {"quit", "exit", "q"}:
            break

        result = bot.ask(q)
        print(f"\n🤖 {result['answer']}")
        if result["sources"]:
            print(f"📁 Sources: {', '.join(result['sources'])}\n")


if __name__ == "__main__":
    main()