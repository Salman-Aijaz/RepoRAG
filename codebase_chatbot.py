"""
🚀 Codebase Explainer AI - FREE VERSION
Uses LOCAL embeddings (no API quota issues!)
Gemini API only for chat (much lower quota usage)
"""

import os
import shutil
import tempfile
import stat
from pathlib import Path
from typing import List
import git
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


class CodebaseExplainerFree:
    """FREE version with local embeddings"""
    
    INCLUDE_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.md'}
    EXCLUDE_FOLDERS = {'node_modules', 'dist', 'build', '.git', '__pycache__', 'venv', 'env', '.next'}
    
    def __init__(self, gemini_api_key: str):
        """Initialize with Gemini for chat ONLY"""
        self.api_key = gemini_api_key
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        # 🔥 FREE LOCAL EMBEDDINGS (no quota!)
        print("📥 Loading local embedding model (first time may take 1-2 min)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ Local embeddings ready!")
        
        # Gemini ONLY for chat (much lower usage)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # Free tier model
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        self.vectorstore = None
        self.qa_chain = None
        
    def clone_repo(self, repo_url: str) -> str:
        """Clone GitHub repo"""
        print(f"🔄 Cloning repository: {repo_url}")
        temp_dir = tempfile.mkdtemp(prefix="repo_")
        
        try:
            git.Repo.clone_from(repo_url, temp_dir, depth=1)
            print(f"✅ Repository cloned to: {temp_dir}")
            return temp_dir
        except Exception as e:
            self._force_delete(temp_dir)
            raise Exception(f"❌ Clone failed: {str(e)}")
    
    def filter_files(self, repo_path: str) -> List[str]:
        """Filter code files"""
        print("🔍 Filtering code files...")
        
        valid_files = []
        repo_path_obj = Path(repo_path)
        
        for file_path in repo_path_obj.rglob('*'):
            if any(excluded in file_path.parts for excluded in self.EXCLUDE_FOLDERS):
                continue
            
            if file_path.is_file() and file_path.suffix in self.INCLUDE_EXTENSIONS:
                valid_files.append(str(file_path))
        
        print(f"✅ Found {len(valid_files)} relevant files")
        return valid_files
    
    def load_and_chunk_files(self, file_paths: List[str]) -> List[dict]:
        """Load and chunk files"""
        print("📄 Loading and chunking files...")
        
        chunks = []
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Smaller chunks for local embeddings
            chunk_overlap=150,
            separators=["\n\n", "\nclass ", "\ndef ", "\nfunction ", "\n", " "]
        )
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                file_chunks = text_splitter.split_text(content)
                
                for chunk in file_chunks:
                    chunks.append({
                        'content': chunk,
                        'metadata': {
                            'file': file_path,
                            'filename': Path(file_path).name
                        }
                    })
            except Exception as e:
                print(f"⚠️  Skipped {file_path}: {str(e)}")
        
        print(f"✅ Created {len(chunks)} chunks")
        return chunks
    
    def create_faiss_index(self, chunks: List[dict]):
        """Create FAISS index with LOCAL embeddings"""
        print("🧠 Creating FAISS index with local embeddings...")
        print("   (This is FREE and unlimited! 🎉)")
        
        texts = [chunk['content'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Create embeddings locally (no API calls!)
        self.vectorstore = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas
        )
        
        print(f"✅ FAISS index created with {len(texts)} vectors (100% FREE!)")
    
    def setup_qa_chain(self):
        """Setup QA chain"""
        print("⚙️  Setting up Q&A chain...")
        
        template = """You are a codebase assistant. Answer questions ONLY based on the provided code context.

STRICT RULES:
1. Use ONLY information from the context below
2. If the answer is not in the context, say "I could not find this in the repository."
3. Always mention the filename when referencing code
4. Do not make assumptions or add information not in the context

Context from repository:
{context}

Question: {question}

Answer (based only on context above):"""

        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        print("✅ Q&A chain ready!")
    
    def _force_delete(self, path: str):
        """Force delete with Windows handling"""
        if not os.path.exists(path):
            return
        
        def handle_remove_readonly(func, path, exc):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except:
                pass
        
        try:
            shutil.rmtree(path, onerror=handle_remove_readonly)
            print(f"🗑️  Deleted temporary repo: {path}\n")
        except:
            try:
                shutil.rmtree(path, ignore_errors=True)
                print(f"🗑️  Deleted temporary repo: {path}\n")
            except:
                print(f"⚠️  Could not delete: {path}\n")
    
    def ingest_repository(self, repo_url: str):
        """Complete ingestion pipeline"""
        print("\n" + "="*60)
        print("🚀 Starting Repository Ingestion (FREE VERSION)")
        print("="*60 + "\n")
        
        temp_dir = None
        try:
            temp_dir = self.clone_repo(repo_url)
            file_paths = self.filter_files(temp_dir)
            
            if not file_paths:
                raise Exception("No valid code files found!")
            
            chunks = self.load_and_chunk_files(file_paths)
            self.create_faiss_index(chunks)
            self.setup_qa_chain()
            
            print("\n" + "="*60)
            print("✅ Repository ingestion complete!")
            print("="*60 + "\n")
            
        finally:
            if temp_dir:
                self._force_delete(temp_dir)
    
    def ask(self, question: str) -> dict:
        """Ask a question"""
        if not self.qa_chain:
            return {"error": "Please ingest a repository first!"}
        
        try:
            result = self.qa_chain.invoke({"query": question})
            
            sources = [doc.metadata.get('filename', 'Unknown') 
                      for doc in result.get('source_documents', [])]
            
            return {
                "answer": result['result'],
                "sources": list(set(sources))
            }
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
    
    def save_index(self, path: str):
        """Save FAISS index"""
        if self.vectorstore:
            self.vectorstore.save_local(path)
            print(f"💾 FAISS index saved to: {path}")
    
    def load_index(self, path: str):
        """Load FAISS index"""
        self.vectorstore = FAISS.load_local(
            path, 
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.setup_qa_chain()
        print(f"📂 FAISS index loaded from: {path}")


def main():
    """Main entry point"""
    print("\n🤖 Codebase Explainer AI - 100% FREE VERSION")
    print("Uses local embeddings (no API quota issues!) 🎉\n")
    
    api_key = input("Enter your Gemini API Key (for chat only): ").strip()
    
    if not api_key:
        print("❌ API key required!")
        return
    
    chatbot = CodebaseExplainerFree(gemini_api_key=api_key)
    
    repo_url = input("\nEnter GitHub repository URL: ").strip()
    
    if not repo_url:
        print("❌ Repository URL required!")
        return
    
    try:
        chatbot.ingest_repository(repo_url)
    except Exception as e:
        print(f"❌ Ingestion failed: {str(e)}")
        return
    
    print("\n💬 Ask questions (type 'quit' to exit)\n")
    
    while True:
        question = input("You: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not question:
            continue
        
        result = chatbot.ask(question)
        
        if 'error' in result:
            print(f"❌ {result['error']}\n")
        else:
            print(f"\n🤖 Bot: {result['answer']}")
            if result['sources']:
                print(f"📁 Sources: {', '.join(result['sources'])}\n")


if __name__ == "__main__":
    main()