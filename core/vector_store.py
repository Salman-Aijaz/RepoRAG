"""
🧠 FAISS Vector Store — 100% FREE (local embeddings)
"""

from typing import List, Dict

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from config.settings import EMBEDDING_MODEL, EMBEDDING_DEVICE


def build_embeddings() -> HuggingFaceEmbeddings:
    """Download (first time) and load the local embedding model."""
    print("📥 Loading local embedding model (first time may take 1-2 min)...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": EMBEDDING_DEVICE},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("✅ Local embeddings ready!")
    return embeddings


def create_faiss_index(chunks: List[Dict], embeddings: HuggingFaceEmbeddings) -> FAISS:
    """Build and return a FAISS vector store from text chunks."""
    print("🧠 Creating FAISS index (100% FREE)...")

    texts     = [c["content"]  for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
    )

    print(f"✅ FAISS index ready with {len(texts)} vectors")
    return vectorstore