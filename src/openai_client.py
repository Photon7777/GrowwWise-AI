from __future__ import annotations

import hashlib
import json
import math
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


DEFAULT_CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


MOCK_EMBEDDING_FEATURES = [
    ["sip", "autopay", "mandate", "installment"],
    ["payment", "debit", "debited", "bank", "refund", "utr", "money"],
    ["kyc", "pan", "verification", "document", "selfie", "address"],
    ["stock", "share", "equity", "exchange"],
    ["order", "pending", "executed", "execution", "limit", "market"],
    ["ipo", "upi", "allotment", "bid", "registrar"],
    ["etf", "exchange traded fund"],
    ["mutual fund", "nav", "scheme"],
    ["redemption", "redeem", "timeline", "business day", "credit"],
    ["login", "otp", "password", "locked", "device", "phone"],
    ["f&o", "future", "futures", "option", "options", "derivative", "margin"],
    ["risk", "loss", "guaranteed", "return", "advice", "market"],
    ["account", "access", "unauthorized", "security"],
    ["legal", "compliance", "complaint", "escalate"],
]


def mock_embedding(text: str, dimensions: int = 64) -> list[float]:
    """Deterministic semantic-ish fallback so Chroma still works without an API key."""
    normalized = " ".join(re.findall(r"[a-z0-9&']+", text.lower()))
    values = [0.0] * dimensions

    for index, keywords in enumerate(MOCK_EMBEDDING_FEATURES):
        values[index] = float(sum(normalized.count(keyword) for keyword in keywords))

    seed = hashlib.sha256(text.encode("utf-8")).digest()
    hash_index = len(MOCK_EMBEDDING_FEATURES)

    while hash_index < dimensions:
        for byte in seed:
            values[hash_index] = ((byte / 127.5) - 1.0) * 0.05
            hash_index += 1
            if hash_index == dimensions:
                break
        seed = hashlib.sha256(seed).digest()

    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


class OpenAIService:
    def __init__(
        self,
        chat_model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        raw_api_key = _get_secret("OPENAI_API_KEY")
        self.api_key = "" if raw_api_key == "your_openai_api_key_here" else raw_api_key
        self.chat_model = chat_model or DEFAULT_CHAT_MODEL
        self.embedding_model = embedding_model or DEFAULT_EMBEDDING_MODEL
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.last_error: str | None = None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            return [mock_embedding(text) for text in texts]

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                encoding_format="float",
            )
            return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
        except Exception as exc:
            self.last_error = str(exc)
            return [mock_embedding(text) for text in texts]

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: str,
    ) -> str:
        if not self.client:
            return fallback

        try:
            response = self.client.responses.create(
                model=self.chat_model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return self._output_text(response) or fallback
        except Exception as exc:
            self.last_error = str(exc)
            return fallback

    def generate_structured(
        self,
        schema_name: str,
        schema: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.client:
            return fallback

        try:
            response = self.client.responses.create(
                model=self.chat_model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    }
                },
            )
            output_text = self._output_text(response)
            return json.loads(output_text) if output_text else fallback
        except Exception as exc:
            self.last_error = str(exc)
            return fallback

    @staticmethod
    def _output_text(response: Any) -> str:
        if hasattr(response, "output_text"):
            return str(response.output_text).strip()

        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    chunks.append(text)
        return "\n".join(chunks).strip()


def _get_secret(name: str) -> str:
    env_value = os.getenv(name, "").strip()
    if env_value:
        return env_value

    try:
        import streamlit as st

        value = st.secrets.get(name, "")
        return str(value).strip() if value else ""
    except Exception:
        return ""
