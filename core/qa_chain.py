"""
💬 RetrievalQA Chain Setup
"""

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import LLM_MODEL, LLM_TEMPERATURE, RETRIEVER_K


PROMPT_TEMPLATE = """
You are a codebase assistant. You have access to the full repository including
Dockerfiles, config files, CI/CD yamls, and source code.

RULES:
1. Answer ONLY from the context provided.
2. If not found, say: "I could not find this in the repository."
3. Always mention the filename when referencing code or config.
4. For Dockerfiles/configs, explain what each section does.

Context:
{context}

Question:
{question}

Answer:
"""


def build_llm(api_key: str) -> ChatGoogleGenerativeAI:
    """Initialise the Gemini LLM."""
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        convert_system_message_to_human=True,
        google_api_key=api_key,
    )


def build_qa_chain(llm: ChatGoogleGenerativeAI, vectorstore: FAISS) -> RetrievalQA:
    """Wire up the retriever + LLM into a RetrievalQA chain."""
    print("⚙️  Setting up Q&A chain...")

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )

    print("✅ Q&A chain ready")
    return chain