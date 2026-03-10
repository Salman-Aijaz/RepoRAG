"""
▶️  Entry point — run this file to start the CLI chatbot
"""

from core.explainer import CodebaseExplainer


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

    bot.ingest_repository(repo_url)

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