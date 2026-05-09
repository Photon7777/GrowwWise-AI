from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.openai_client import OpenAIService
from src.utils import DATA_DIR, format_currency, format_percent


PORTFOLIO_SYSTEM_PROMPT = """You are GrowwWise, a fintech education assistant.
Explain portfolio risk in simple language for a beginner retail investor.
Discuss concentration risk, high-risk exposure, diversification, and general educational suggestions.
Do not recommend specific stocks to buy or sell.
Do not promise returns.
Always include: 'This is for educational purposes and not financial advice.'"""


def load_portfolio(path: str | Path | None = None) -> pd.DataFrame:
    csv_path = Path(path) if path else DATA_DIR / "sample_portfolio.csv"
    df = pd.read_csv(csv_path)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df


def calculate_portfolio_metrics(df: pd.DataFrame) -> dict[str, Any]:
    total_value = float(df["amount"].sum())
    if total_value <= 0:
        return {
            "total_value": 0.0,
            "type_allocations": {},
            "risk_allocations": {},
            "asset_allocations": {},
        }

    type_allocations = ((df.groupby("type")["amount"].sum() / total_value) * 100).round(2).to_dict()
    risk_allocations = ((df.groupby("risk_level")["amount"].sum() / total_value) * 100).round(2).to_dict()
    asset_allocations = ((df.groupby("asset_name")["amount"].sum() / total_value) * 100).round(2).to_dict()

    return {
        "total_value": total_value,
        "type_allocations": type_allocations,
        "risk_allocations": risk_allocations,
        "asset_allocations": asset_allocations,
    }


def generate_portfolio_explanation(df: pd.DataFrame, metrics: dict[str, Any] | None = None) -> str:
    metrics = metrics or calculate_portfolio_metrics(df)
    fallback = fallback_portfolio_explanation(metrics)
    portfolio_table = df.to_csv(index=False)
    user_prompt = f"""Portfolio CSV:
{portfolio_table}

Calculated metrics:
Total value: {metrics["total_value"]}
Allocation by asset type: {metrics["type_allocations"]}
Allocation by risk level: {metrics["risk_allocations"]}
Allocation by asset: {metrics["asset_allocations"]}

Write a concise portfolio risk explanation with practical, general education points."""

    service = OpenAIService()
    return service.generate_text(PORTFOLIO_SYSTEM_PROMPT, user_prompt, fallback)


def analyze_portfolio(path: str | Path | None = None) -> dict[str, Any]:
    df = load_portfolio(path)
    metrics = calculate_portfolio_metrics(df)
    explanation = generate_portfolio_explanation(df, metrics)
    return {
        "dataframe": df,
        "metrics": metrics,
        "explanation": explanation,
    }


def fallback_portfolio_explanation(metrics: dict[str, Any]) -> str:
    total = metrics.get("total_value", 0.0)
    risk_allocations = metrics.get("risk_allocations", {})
    type_allocations = metrics.get("type_allocations", {})
    asset_allocations = metrics.get("asset_allocations", {})

    top_asset = max(asset_allocations.items(), key=lambda item: item[1], default=("No asset", 0))
    top_type = max(type_allocations.items(), key=lambda item: item[1], default=("No asset type", 0))
    high_risk = float(risk_allocations.get("High", 0.0))

    concentration_note = (
        f"The largest single holding is {top_asset[0]} at {format_percent(float(top_asset[1]))} of the portfolio. "
        "That is worth watching because a single large position can influence overall returns."
    )
    if float(top_asset[1]) < 40:
        concentration_note += " It is not an extreme concentration, but it is still the biggest driver in this sample."

    high_risk_note = (
        f"High-risk exposure is {format_percent(high_risk)}. Higher-risk assets can create more volatility, "
        "so the investor should understand time horizon, loss tolerance, and liquidity needs."
    )

    diversification_note = (
        f"The portfolio is spread across asset types, with the largest type being {top_type[0]} at "
        f"{format_percent(float(top_type[1]))}. Diversification across asset classes can reduce dependence on one market segment, "
        "but it does not remove market risk."
    )

    return (
        f"Total portfolio value is {format_currency(float(total))}.\n\n"
        f"- Concentration risk: {concentration_note}\n"
        f"- High-risk exposure: {high_risk_note}\n"
        f"- Diversification: {diversification_note}\n"
        "- General education: Review whether the risk mix matches the investor's goals, emergency needs, and investment horizon. "
        "Avoid making decisions based only on short-term market predictions.\n\n"
        "This is for educational purposes and not financial advice."
    )
