"""
🧪 Test Script - Verify everything is working
"""

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    try:
        import langchain
        print("✅ langchain")
    except ImportError:
        print("❌ langchain - Run: pip install langchain")
        return False
    
    try:
        from langchain_community.vectorstores import FAISS
        print("✅ langchain-community (FAISS)")
    except ImportError:
        print("❌ langchain-community - Run: pip install langchain-community")
        return False
    
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        print("✅ langchain-google-genai")
    except ImportError:
        print("❌ langchain-google-genai - Run: pip install langchain-google-genai")
        return False
    
    try:
        import faiss
        print("✅ faiss-cpu")
    except ImportError:
        print("❌ faiss-cpu - Run: pip install faiss-cpu")
        return False
    
    try:
        import git
        print("✅ gitpython")
    except ImportError:
        print("❌ gitpython - Run: pip install gitpython")
        return False
    
    return True


def test_api_key():
    """Test if API key is valid"""
    print("\nTesting Gemini API key...")
    
    api_key = input("Enter your Gemini API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        import os
        
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Try to initialize embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Try a simple embedding
        test_text = "Hello, this is a test"
        result = embeddings.embed_query(test_text)
        
        if result and len(result) > 0:
            print(f"✅ API key is valid! (Embedding dimension: {len(result)})")
            return True
        else:
            print("❌ API key test failed")
            return False
            
    except Exception as e:
        print(f"❌ API key error: {str(e)}")
        return False


def test_git():
    """Test if git is available"""
    print("\nTesting git...")
    
    try:
        import git
        
        # Check git version
        git_version = git.cmd.Git().version()
        print(f"✅ Git installed: {git_version}")
        return True
        
    except Exception as e:
        print(f"❌ Git error: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Running Tests")
    print("=" * 60 + "\n")
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed. Install missing packages.")
        return
    
    # Test 2: Git
    if not test_git():
        print("\n❌ Git test failed. Install git.")
        return
    
    # Test 3: API Key
    if not test_api_key():
        print("\n❌ API key test failed.")
        return
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! You're ready to use the chatbot!")
    print("=" * 60)
    print("\nRun: python codebase_chatbot.py")


if __name__ == "__main__":
    run_all_tests()