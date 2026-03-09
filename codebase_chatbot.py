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
        # Code files
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.go', '.rs',
        '.rb', '.php', '.cs', '.swift', '.kt',
        # Config & infra files
        '.yml', '.yaml', '.toml', '.ini', '.cfg',
        '.env', '.env.example', '.sh', '.bash',
        '.xml', '.json', '.jsonc',
        # Docs
        '.md', '.txt', '.rst',
        # Web
        '.html', '.css', '.scss',
        # SQL
        '.sql',
    }

    # Files with NO extension that should be included (exact filename match)
    INCLUDE_EXACT_NAMES = {
        'Dockerfile', 'Makefile', 'Procfile',
        '.gitignore', '.dockerignore', '.env',
        'docker-compose', 'nginx.conf',
    }

    EXCLUDE_FOLDERS = {
        'node_modules', '.git', '__pycache__',
        'venv', 'env', '.venv',
        '.next', '.nuxt',
        'coverage', '.pytest_cache',
        '.mypy_cache', '.ruff_cache',
    }

    # Only exclude build/dist if they have specific markers
    SOFT_EXCLUDE_FOLDERS = {
        'dist', 'build',
    }

    def __init__(self):
        """Initialize Gemini from ENV and local embeddings"""

        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "❌ GOOGLE_API_KEY not found. Please set it in .env file"
            )

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            convert_system_message_to_human=True
        )

        print("✅ Gemini API key loaded from ENV")

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

    def _should_exclude(self, path: Path) -> bool:
        """
        Check if path should be excluded.
        Hard excludes: always skip.
        Soft excludes (dist/build): only skip if they contain
        minified/compiled artifacts (no source maps, etc.)
        """
        parts = path.parts

        # Hard exclude check
        for part in parts:
            if part in self.EXCLUDE_FOLDERS:
                return True

        # Soft exclude: skip dist/build ONLY if file looks compiled
        for part in parts:
            if part in self.SOFT_EXCLUDE_FOLDERS:
                # Keep config files even in build/dist
                if path.suffix in {'.yml', '.yaml', '.json', '.md', '.txt'}:
                    return False
                # Skip minified JS/CSS
                if path.suffix in {'.js', '.css'} and (
                    '.min.' in path.name or path.name.endswith('.min.js')
                ):
                    return True
                # Otherwise keep (could be compiled but useful)
                return True

        return False

    def filter_files(self, repo_path: str) -> List[str]:
        print("🔍 Filtering code files...")
        valid_files = []
        skipped = 0

        for path in Path(repo_path).rglob("*"):
            if not path.is_file():
                continue

            if self._should_exclude(path):
                skipped += 1
                continue

            # Match by extension
            if path.suffix.lower() in self.INCLUDE_EXTENSIONS:
                valid_files.append(str(path))
                continue

            # Match by exact filename (e.g. Dockerfile, Makefile)
            if path.name in self.INCLUDE_EXACT_NAMES:
                valid_files.append(str(path))
                continue

            # Match files like "docker-compose.override.yml" already caught by .yml
            # But also catch extensionless files with known names
            if path.stem in self.INCLUDE_EXACT_NAMES and path.suffix == '':
                valid_files.append(str(path))
                continue

        print(f"✅ Found {len(valid_files)} relevant files (skipped ~{skipped} excluded)")

        # Debug: show root-level files picked up
        root = Path(repo_path)
        root_files = [f for f in valid_files if Path(f).parent == root]
        if root_files:
            print(f"📁 Root-level files included: {[Path(f).name for f in root_files]}")

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

                # Skip empty files
                if not content.strip():
                    continue

                # Skip very large files (likely generated/minified)
                if len(content) > 200_000:
                    print(f"⚠️  Skipped large file (>200KB): {Path(file).name}")
                    continue

                file_chunks = splitter.split_text(content)

                for chunk in file_chunks:
                    chunks.append({
                        "content": chunk,
                        "metadata": {
                            "file": file,
                            "filename": Path(file).name,
                            # Relative path for cleaner display
                            "rel_path": str(Path(file))
                        }
                    })

            except Exception as e:
                print(f"⚠️  Skipped {file}: {e}")

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
You are a codebase assistant. You have access to the full repository including
Dockerfiles, config files, CI/CD yamls, and source code.

RULES:
1. Answer ONLY from the context provided
2. If not found, say: "I could not find this in the repository."
3. Always mention the filename when referencing code or config
4. For Dockerfiles/configs, explain what each section does

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
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
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

            if not files:
                print("❌ No files found! Check repo URL or file types.")
                return

            chunks = self.load_and_chunk_files(files)

            if not chunks:
                print("❌ No chunks created! Files might be empty.")
                return

            self.create_faiss_index(chunks)
            self.setup_qa_chain()
            print("\n✅ Repository ingestion complete\n")
        finally:
            if temp_dir:
                self._force_delete(temp_dir)

    # ----------------------------------------------------

    def ask(self, question: str) -> dict:
        if not self.qa_chain:
            return {"answer": "❌ No repo ingested yet.", "sources": []}

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