from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings

from src.guardrails import is_risky_financial_advice, safe_financial_response
from src.openai_client import OpenAIService
from src.utils import load_help_docs


SYSTEM_PROMPT = """You are GrowwWise, an AI support copilot for a fintech investing platform.
Help users understand support issues and investing concepts in simple language.
Use only the retrieved context for platform-support questions.
Do not provide direct buy/sell recommendations.
Do not promise guaranteed returns.
For payment failures, KYC issues, account access, order execution issues, or legal/compliance issues, recommend human escalation.
For investing-related answers, add: 'This is for educational purposes and not financial advice.'"""


class RAGAssistant:
    def __init__(self, docs_path: str | None = None) -> None:
        self.openai = OpenAIService()
        self.docs = load_help_docs(docs_path)
        self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        mode = "openai" if self.openai.enabled else "mock"
        self.collection = self.client.get_or_create_collection(name=f"growwwise_help_docs_{mode}")
        self._build_index()

    def _doc_text(self, doc: dict[str, Any]) -> str:
        return f"{doc['title']}\nCategory: {doc['category']}\n{doc['content']}"

    def _build_index(self) -> None:
        if self.collection.count() > 0:
            return

        ids = [doc["id"] for doc in self.docs]
        texts = [self._doc_text(doc) for doc in self.docs]
        embeddings = self.openai.create_embeddings(texts)
        metadatas = [
            {
                "title": doc["title"],
                "category": doc["category"],
                "source_id": doc["id"],
            }
            for doc in self.docs
        ]

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        query_embedding = self.openai.create_embeddings([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        return [
            {
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]

    def answer(self, query: str) -> dict[str, Any]:
        if is_risky_financial_advice(query):
            return {
                "answer": safe_financial_response(),
                "sources": [],
                "guardrail_triggered": True,
            }

        sources = self.retrieve(query)
        return self.answer_from_sources(query, sources)

    def answer_from_sources(self, query: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
        context = "\n\n---\n\n".join(source["content"] for source in sources)
        fallback = self._fallback_answer(query, sources)
        user_prompt = f"""User question:
{query}

Retrieved context:
{context}

Answer the user in a concise, helpful way. If the context does not contain enough information, say what is known from the context and recommend contacting support."""

        answer = self.openai.generate_text(SYSTEM_PROMPT, user_prompt, fallback)
        return {
            "answer": answer,
            "sources": sources,
            "guardrail_triggered": False,
        }

    def _fallback_answer(self, query: str, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "I could not find a relevant help document. Please contact support for this issue."

        top_source = sources[0]
        metadata = top_source["metadata"]
        content = top_source["content"].split("\n", maxsplit=2)[-1]
        escalation_categories = {"Payments", "KYC", "Account", "Orders"}
        escalation_note = ""

        if metadata.get("category") in escalation_categories:
            escalation_note = (
                "\n\nBecause this may involve payments, account access, compliance, or order execution, "
                "please escalate to a human support agent with relevant IDs, timestamps, and bank or order references."
            )

        disclaimer = ""
        if any(word in query.lower() for word in ["invest", "stock", "etf", "mutual fund", "f&o", "return"]):
            disclaimer = "\n\nThis is for educational purposes and not financial advice."

        return f"Based on the GrowwWise help docs: {content}{escalation_note}{disclaimer}"
