from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

import pandas as pd

from src.openai_client import OpenAIService
from src.utils import BASE_DIR, DATA_DIR, format_percent


TICKETS_CSV = DATA_DIR / "support_tickets.csv"


BUSINESS_INSIGHTS_SYSTEM_PROMPT = """You are GrowwWise Analytics, an AI analyst for a fintech support team.
Use only the aggregated dashboard statistics provided.
Write concise stakeholder-friendly insights.
Focus on ticket drivers, slow categories, escalation drivers, low CSAT segments, and practical operational recommendations.
Do not invent exact numbers that are not in the summary."""


DATA_QA_SYSTEM_PROMPT = """You answer questions about a fintech support analytics dataset.
Use only the aggregated statistics provided, not raw rows.
Be concise, explain the business meaning, and recommend what the support team should inspect next."""


def ensure_support_dataset(path: str | Path | None = None) -> Path:
    csv_path = Path(path) if path else TICKETS_CSV
    if csv_path.exists():
        return csv_path

    script_path = BASE_DIR / "scripts" / "generate_dataset.py"
    if not script_path.exists():
        raise FileNotFoundError("Missing scripts/generate_dataset.py; cannot generate support ticket dataset.")

    subprocess.run([sys.executable, str(script_path)], cwd=str(BASE_DIR), check=True)
    return csv_path


def load_support_tickets(path: str | Path | None = None) -> pd.DataFrame:
    csv_path = ensure_support_dataset(path)
    df = pd.read_csv(csv_path)
    return prepare_support_tickets(df)


def prepare_support_tickets(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["created_date"] = pd.to_datetime(cleaned["created_date"], errors="coerce")
    cleaned["resolution_time_hours"] = pd.to_numeric(cleaned["resolution_time_hours"], errors="coerce")
    cleaned["csat_score"] = pd.to_numeric(cleaned["csat_score"], errors="coerce")

    if cleaned["human_escalation_required"].dtype != bool:
        cleaned["human_escalation_required"] = (
            cleaned["human_escalation_required"].astype(str).str.lower().isin(["true", "1", "yes"])
        )

    text_columns = [
        "ticket_id",
        "user_id",
        "issue_category",
        "issue_subcategory",
        "user_message",
        "urgency",
        "priority",
        "sentiment",
        "status",
        "channel",
        "city",
        "state",
        "app_version",
        "customer_segment",
    ]
    for column in text_columns:
        cleaned[column] = cleaned[column].fillna("Unknown").astype(str)

    return cleaned.dropna(subset=["created_date"]).sort_values("created_date").reset_index(drop=True)


def filter_support_tickets(
    df: pd.DataFrame,
    date_range: tuple[Any, Any] | list[Any] | None = None,
    categories: Iterable[str] | None = None,
    priorities: Iterable[str] | None = None,
    statuses: Iterable[str] | None = None,
    channels: Iterable[str] | None = None,
    customer_segments: Iterable[str] | None = None,
) -> pd.DataFrame:
    filtered = df.copy()

    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[
            (filtered["created_date"].dt.normalize() >= start_date.normalize())
            & (filtered["created_date"].dt.normalize() <= end_date.normalize())
        ]

    filtered = _filter_in(filtered, "issue_category", categories)
    filtered = _filter_in(filtered, "priority", priorities)
    filtered = _filter_in(filtered, "status", statuses)
    filtered = _filter_in(filtered, "channel", channels)
    filtered = _filter_in(filtered, "customer_segment", customer_segments)

    return filtered.reset_index(drop=True)


def calculate_kpis(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    if total == 0:
        return {
            "total_tickets": 0,
            "avg_resolution_time_hours": 0.0,
            "human_escalation_rate": 0.0,
            "avg_csat_score": 0.0,
            "high_priority_tickets": 0,
            "open_tickets": 0,
        }

    return {
        "total_tickets": int(total),
        "avg_resolution_time_hours": round(float(df["resolution_time_hours"].mean()), 1),
        "human_escalation_rate": round(float(df["human_escalation_required"].mean() * 100), 1),
        "avg_csat_score": round(float(df["csat_score"].mean()), 2),
        "high_priority_tickets": int((df["priority"] == "High").sum()),
        "open_tickets": int((df["status"] == "Open").sum()),
    }


def summarize_for_ai(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    if total == 0:
        return {"total_tickets": 0, "message": "No tickets match the selected filters."}

    category_counts = df["issue_category"].value_counts()
    category_share = (category_counts / total * 100).round(1)
    high_priority = df[df["priority"] == "High"]

    return {
        "kpis": calculate_kpis(df),
        "category_share_percent": _series_to_dict(category_share),
        "top_subcategories": _series_to_dict(df["issue_subcategory"].value_counts().head(10)),
        "status_mix": _series_to_dict(df["status"].value_counts()),
        "priority_mix": _series_to_dict(df["priority"].value_counts()),
        "sentiment_mix": _series_to_dict(df["sentiment"].value_counts()),
        "channel_distribution": _series_to_dict(df["channel"].value_counts()),
        "avg_resolution_by_category_hours": _series_to_dict(
            df.groupby("issue_category")["resolution_time_hours"].mean().sort_values(ascending=False).round(1)
        ),
        "escalation_rate_by_category_percent": _series_to_dict(
            (df.groupby("issue_category")["human_escalation_required"].mean() * 100)
            .sort_values(ascending=False)
            .round(1)
        ),
        "escalation_rate_by_subcategory_percent": _series_to_dict(
            (df.groupby("issue_subcategory")["human_escalation_required"].mean() * 100)
            .sort_values(ascending=False)
            .round(1)
            .head(10)
        ),
        "avg_csat_by_customer_segment": _series_to_dict(
            df.groupby("customer_segment")["csat_score"].mean().sort_values().round(2)
        ),
        "avg_csat_by_category": _series_to_dict(df.groupby("issue_category")["csat_score"].mean().sort_values().round(2)),
        "high_priority_tickets_by_channel": _series_to_dict(high_priority["channel"].value_counts()),
        "volume_last_14_days": _series_to_dict(
            df.groupby(df["created_date"].dt.date)["ticket_id"].count().tail(14)
        ),
    }


def generate_business_insights(df: pd.DataFrame) -> str:
    summary = summarize_for_ai(df)
    fallback = fallback_business_insights(summary)
    service = OpenAIService()
    prompt = f"""Aggregated dashboard summary:
{json.dumps(summary, indent=2)}

Write 4-6 concise bullets for Groww-style support and product stakeholders."""
    return service.generate_text(BUSINESS_INSIGHTS_SYSTEM_PROMPT, prompt, fallback)


def answer_dataset_question(question: str, df: pd.DataFrame) -> str:
    summary = summarize_for_ai(df)
    fallback = fallback_dataset_answer(question, summary)
    service = OpenAIService()
    prompt = f"""Question:
{question}

Aggregated dashboard summary:
{json.dumps(summary, indent=2)}

Answer from the summary statistics only."""
    return service.generate_text(DATA_QA_SYSTEM_PROMPT, prompt, fallback)


def fallback_business_insights(summary: dict[str, Any]) -> str:
    if summary.get("total_tickets") == 0:
        return "No tickets match the selected filters, so there is not enough data to generate business insights."

    kpis = summary["kpis"]
    top_categories = list(summary["category_share_percent"].items())[:3]
    slowest = _first_item(summary["avg_resolution_by_category_hours"])
    highest_escalation = _first_item(summary["escalation_rate_by_category_percent"])
    lowest_csat = _first_item(summary["avg_csat_by_customer_segment"])

    top_text = ", ".join(f"{name} ({value}%)" for name, value in top_categories)
    return (
        f"- Main ticket drivers are {top_text}, representing the biggest visible support load in the filtered data.\n"
        f"- The slowest category is {slowest[0]} with an average resolution time of {slowest[1]} hours.\n"
        f"- The highest escalation rate is in {highest_escalation[0]} at {format_percent(float(highest_escalation[1]))}.\n"
        f"- The lowest CSAT segment is {lowest_csat[0]} with an average score of {lowest_csat[1]}.\n"
        f"- Support should prioritize payment and onboarding clarity, faster status notifications, and automation for repeat issues.\n"
        f"- Current KPI snapshot: {kpis['total_tickets']} tickets, {kpis['human_escalation_rate']}% escalation rate, "
        f"{kpis['avg_csat_score']} average CSAT."
    )


def fallback_dataset_answer(question: str, summary: dict[str, Any]) -> str:
    if summary.get("total_tickets") == 0:
        return "No tickets match the selected filters, so I cannot answer this from the current dashboard view."

    text = question.lower()
    if "resolution" in text and ("highest" in text or "longest" in text or "slow" in text):
        category, value = _first_item(summary["avg_resolution_by_category_hours"])
        return f"{category} has the highest average resolution time at {value} hours in the filtered data."

    if "lowest csat" in text or ("csat" in text and "lowest" in text):
        segment, value = _first_item(summary["avg_csat_by_customer_segment"])
        return f"{segment} has the lowest average CSAT at {value}. This segment may need clearer communication or faster resolution."

    if "escalat" in text or "human" in text:
        top = list(summary["escalation_rate_by_subcategory_percent"].items())[:3]
        top_text = ", ".join(f"{name} ({value}%)" for name, value in top)
        return f"The top escalation drivers by subcategory are {top_text}."

    if "channel" in text and ("high" in text or "priority" in text):
        top = list(summary["high_priority_tickets_by_channel"].items())
        top_text = ", ".join(f"{name}: {value}" for name, value in top)
        return f"High-priority tickets are most concentrated by channel as follows: {top_text}."

    if "improve" in text or "prioritize" in text or "first" in text:
        highest_escalation = _first_item(summary["escalation_rate_by_category_percent"])
        slowest = _first_item(summary["avg_resolution_by_category_hours"])
        return (
            f"The team should improve {highest_escalation[0]} first because it has the highest escalation rate "
            f"({highest_escalation[1]}%). Also inspect {slowest[0]}, which has the slowest average resolution time "
            f"({slowest[1]} hours)."
        )

    return fallback_business_insights(summary)


def _filter_in(df: pd.DataFrame, column: str, selected: Iterable[str] | None) -> pd.DataFrame:
    values = list(selected or [])
    if not values:
        return df
    return df[df[column].isin(values)]


def _series_to_dict(series: pd.Series) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in series.items():
        if hasattr(key, "isoformat"):
            key = key.isoformat()
        if pd.isna(value):
            continue
        if isinstance(value, (int, float)):
            result[str(key)] = round(float(value), 2)
        else:
            result[str(key)] = value
    return result


def _first_item(mapping: dict[str, Any]) -> tuple[str, Any]:
    if not mapping:
        return ("No data", 0)
    return next(iter(mapping.items()))
