"""
🚀 Codebase Explainer AI - FREE VERSION
Uses LOCAL embeddings (no API quota issues!)
Gemini API only for chat (ENV based)
"""

import os
import shutil
import tempfile
import stat
from pathlib import Path
from typing import List

import git
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


# 🔥 Load ENV variables from .env
load_dotenv()


class CodebaseExplainerFree:
    """FREE version with local embeddings"""

    INCLUDE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.go', '.rs', '.md'
    }

    EXCLUDE_FOLDERS = {
        'node_modules', 'dist', 'build', '.git',
        '__pycache__', 'venv', 'env', '.next'
    }

    def __init__(self):
        """Initialize Gemini from ENV and local embeddings"""

        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "❌ GOOGLE_API_KEY not found. Please set it in .env file"
            )

        # Gemini automatically reads GOOGLE_API_KEY from env
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            convert_system_message_to_human=True
        )

        print("✅ Gemini API key loaded from ENV")

        # 🔥 FREE LOCAL EMBEDDINGS
        print("📥 Loading local embedding model (first time may take 1-2 min)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        print("✅ Local embeddings ready!")

        self.vectorstore = None
        self.qa_chain = None

    # ----------------------------------------------------

    def clone_repo(self, repo_url: str) -> str:
        print(f"🔄 Cloning repository: {repo_url}")
        temp_dir = tempfile.mkdtemp(prefix="repo_")

        try:
            git.Repo.clone_from(repo_url, temp_dir, depth=1)
            print(f"✅ Repository cloned to: {temp_dir}")
            return temp_dir
        except Exception as e:
            self._force_delete(temp_dir)
            raise RuntimeError(f"Clone failed: {e}")

    # ----------------------------------------------------

    def filter_files(self, repo_path: str) -> List[str]:
        print("🔍 Filtering code files...")
        valid_files = []

        for path in Path(repo_path).rglob("*"):
            if any(ex in path.parts for ex in self.EXCLUDE_FOLDERS):
                continue

            if path.is_file() and path.suffix in self.INCLUDE_EXTENSIONS:
                valid_files.append(str(path))

        print(f"✅ Found {len(valid_files)} relevant files")
        return valid_files

    # ----------------------------------------------------

    def load_and_chunk_files(self, files: List[str]) -> List[dict]:
        print("📄 Loading and chunking files...")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\nclass ", "\ndef ", "\nfunction ", "\n", " "]
        )

        chunks = []

        for file in files:
            try:
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for chunk in splitter.split_text(content):
                    chunks.append({
                        "content": chunk,
                        "metadata": {
                            "file": file,
                            "filename": Path(file).name
                        }
                    })
            except Exception as e:
                print(f"⚠️ Skipped {file}: {e}")

        print(f"✅ Created {len(chunks)} chunks")
        return chunks

    # ----------------------------------------------------

    def create_faiss_index(self, chunks: List[dict]):
        print("🧠 Creating FAISS index (100% FREE)")

        texts = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        self.vectorstore = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas
        )

        print(f"✅ FAISS index ready with {len(texts)} vectors")

    # ----------------------------------------------------

    def setup_qa_chain(self):
        print("⚙️ Setting up Q&A chain")

        template = """
You are a codebase assistant.

RULES:
1. Answer ONLY from the context
2. If not found, say: "I could not find this in the repository."
3. Mention filename when referencing code

Context:
{context}

Question:
{question}

Answer:
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

        print("✅ Q&A chain ready")

    # ----------------------------------------------------

    def ingest_repository(self, repo_url: str):
        print("\n🚀 Starting Repository Ingestion\n")

        temp_dir = None
        try:
            temp_dir = self.clone_repo(repo_url)
            files = self.filter_files(temp_dir)
            chunks = self.load_and_chunk_files(files)
            self.create_faiss_index(chunks)
            self.setup_qa_chain()
            print("\n✅ Repository ingestion complete\n")
        finally:
            if temp_dir:
                self._force_delete(temp_dir)

    # ----------------------------------------------------

    def ask(self, question: str) -> dict:
        result = self.qa_chain.invoke({"query": question})

        sources = {
            doc.metadata.get("filename", "unknown")
            for doc in result.get("source_documents", [])
        }

        return {
            "answer": result["result"],
            "sources": list(sources)
        }

    # ----------------------------------------------------

    def _force_delete(self, path: str):
        def handle(func, p, _):
            os.chmod(p, stat.S_IWRITE)
            func(p)

        shutil.rmtree(path, onerror=handle, ignore_errors=True)


# ======================================================

def main():
    print("\n🤖 Codebase Explainer AI (ENV + FREE MODE)\n")

    try:
        bot = CodebaseExplainerFree()
    except RuntimeError as e:
        print(e)
        return

    repo_url = input("Enter GitHub repository URL: ").strip()
    if not repo_url:
        print("❌ Repository URL required")
        return

    bot.ingest_repository(repo_url)

    print("💬 Ask questions (type 'quit' to exit)\n")

    while True:
        q = input("You: ").strip()
        if q.lower() in {"quit", "exit", "q"}:
            break

        result = bot.ask(q)
        print(f"\n🤖 {result['answer']}")
        if result["sources"]:
            print(f"📁 Sources: {', '.join(result['sources'])}\n")


if __name__ == "__main__":
    main()