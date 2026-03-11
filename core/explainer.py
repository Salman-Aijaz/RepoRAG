"""
🤖 CodebaseExplainer — orchestrates ingestion + Q&A
"""

import os
from dotenv import load_dotenv

from utils.repo_manager import resolve_and_clone, force_delete
from utils.file_filter  import filter_files
from utils.chunker      import load_and_chunk_files
from core.vector_store  import build_embeddings, create_faiss_index
from core.qa_chain      import build_llm, build_qa_chain

load_dotenv()


class CodebaseExplainer:
    """Ingest a GitHub repo and answer questions about it."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "❌ GOOGLE_API_KEY not found. Please set it in your .env file."
            )

        self.llm        = build_llm(self.api_key)
        self.embeddings = build_embeddings()
        self.qa_chain   = None

        print("✅ Gemini API key loaded from ENV")

    # ── Public API ──────────────────────────────────────────────

    def ingest_repository(self, repo_url: str, token: str = None) -> None:
        """Clone repo → filter → chunk → index → build chain."""
        print("\n🚀 Starting Repository Ingestion\n")

        temp_dir = None
        try:
            temp_dir = resolve_and_clone(repo_url, token)
            files    = filter_files(temp_dir)

            if not files:
                print("❌ No files found! Check repo URL or file types.")
                return

            chunks = load_and_chunk_files(files)

            if not chunks:
                print("❌ No chunks created! Files might be empty.")
                return

            vectorstore   = create_faiss_index(chunks, self.embeddings)
            self.qa_chain = build_qa_chain(self.llm, vectorstore)

            print("\n✅ Repository ingestion complete\n")

        finally:
            if temp_dir:
                force_delete(temp_dir)

    def ask(self, question: str) -> dict:
        """Ask a question. Returns answer + source filenames."""
        if not self.qa_chain:
            return {"answer": "❌ No repo ingested yet.", "sources": []}

        result  = self.qa_chain.invoke({"query": question})
        sources = {
            doc.metadata.get("filename", "unknown")
            for doc in result.get("source_documents", [])
        }

        return {
            "answer":  result["result"],
            "sources": list(sources),
        }