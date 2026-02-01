"""
🚀 Advanced Example - With Index Saving/Loading
"""

from codebase_chatbot import CodebaseExplainer
import os
from pathlib import Path


def chat_with_saved_index():
    """Example: Load saved index and chat"""
    api_key = os.getenv("GOOGLE_API_KEY") or input("Enter Gemini API Key: ")
    
    chatbot = CodebaseExplainer(gemini_api_key=api_key)
    
    # Load existing index
    index_path = "faiss_index"
    if Path(index_path).exists():
        print("📂 Loading saved index...")
        chatbot.load_index(index_path)
    else:
        print("❌ No saved index found!")
        return
    
    # Chat loop
    print("\n💬 Ask questions (type 'quit' to exit)\n")
    
    while True:
        question = input("You: ").strip()
        
        if question.lower() in ['quit', 'exit']:
            break
        
        result = chatbot.ask(question)
        print(f"\n🤖 {result['answer']}")
        if result.get('sources'):
            print(f"📁 Sources: {', '.join(result['sources'])}\n")


def ingest_and_save():
    """Example: Ingest repo and save index for later use"""
    api_key = os.getenv("GOOGLE_API_KEY") or input("Enter Gemini API Key: ")
    
    chatbot = CodebaseExplainer(gemini_api_key=api_key)
    
    # Popular repos for testing
    example_repos = {
        "1": "https://github.com/openai/whisper",
        "2": "https://github.com/gradio-app/gradio",
        "3": "https://github.com/langchain-ai/langchain",
    }
    
    print("\n📚 Example Repositories:")
    for key, url in example_repos.items():
        print(f"{key}. {url}")
    
    choice = input("\nChoose (1-3) or enter custom URL: ").strip()
    
    repo_url = example_repos.get(choice, choice)
    
    # Ingest
    chatbot.ingest_repository(repo_url)
    
    # Save index
    chatbot.save_index("faiss_index")
    
    print("\n✅ Index saved! You can now use chat_with_saved_index()")


def quick_test():
    """Quick test with a small repo"""
    api_key = os.getenv("GOOGLE_API_KEY") or input("Enter Gemini API Key: ")
    
    chatbot = CodebaseExplainer(gemini_api_key=api_key)
    
    # Small test repo
    test_repo = "https://github.com/pallets/flask"
    
    print(f"\n🧪 Testing with: {test_repo}\n")
    
    chatbot.ingest_repository(test_repo)
    
    # Auto-ask some questions
    questions = [
        "What is this repository about?",
        "How does routing work?",
        "What are the main components?"
    ]
    
    for q in questions:
        print(f"\n❓ Question: {q}")
        result = chatbot.ask(q)
        print(f"🤖 Answer: {result['answer']}")
        print(f"📁 Sources: {', '.join(result.get('sources', []))}\n")
        print("-" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "save":
            ingest_and_save()
        elif sys.argv[1] == "chat":
            chat_with_saved_index()
        elif sys.argv[1] == "test":
            quick_test()
    else:
        print("""
🚀 Advanced Examples

Usage:
  python advanced_example.py save   # Ingest repo and save index
  python advanced_example.py chat   # Chat with saved index
  python advanced_example.py test   # Quick test
        """)