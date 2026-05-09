from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def load_help_docs(path: str | Path | None = None) -> list[dict[str, Any]]:
    docs_path = Path(path) if path else DATA_DIR / "help_docs.json"
    docs = load_json(docs_path)
    if not isinstance(docs, list):
        raise ValueError("Help docs must be a list of document objects.")
    return docs


def format_currency(amount: float) -> str:
    return f"Rs. {amount:,.0f}"


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def pydantic_schema(model_cls: Any) -> dict[str, Any]:
    if hasattr(model_cls, "model_json_schema"):
        return model_cls.model_json_schema()
    return model_cls.schema()


def validate_pydantic(model_cls: Any, data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        if hasattr(model_cls, "model_validate"):
            return model_cls.model_validate(data).model_dump()
        return model_cls.parse_obj(data).dict()
    except Exception:
        return fallback
