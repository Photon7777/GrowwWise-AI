from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from src.guardrails import is_risky_financial_advice
from src.openai_client import OpenAIService
from src.utils import validate_pydantic


Category = Literal[
    "KYC",
    "SIP",
    "Mutual Funds",
    "Stocks",
    "IPO",
    "Payments",
    "Orders",
    "Account",
    "Risky Financial Advice",
    "General Education",
    "Human Escalation",
]


class IssueClassification(BaseModel):
    category: Category
    urgency: Literal["Low", "Medium", "High"]
    requires_human: bool
    reason: str
    suggested_next_step: str


ISSUE_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "category": {
            "type": "string",
            "enum": [
                "KYC",
                "SIP",
                "Mutual Funds",
                "Stocks",
                "IPO",
                "Payments",
                "Orders",
                "Account",
                "Risky Financial Advice",
                "General Education",
                "Human Escalation",
            ],
        },
        "urgency": {"type": "string", "enum": ["Low", "Medium", "High"]},
        "requires_human": {"type": "boolean"},
        "reason": {"type": "string"},
        "suggested_next_step": {"type": "string"},
    },
    "required": ["category", "urgency", "requires_human", "reason", "suggested_next_step"],
}


SYSTEM_PROMPT = """Classify fintech support messages for GrowwWise.
Return only structured JSON matching the schema.
Mark high urgency for money debited but failed transactions, account locks, repeated KYC rejection, order execution problems, angry or frustrated users, and legal or compliance issues.
Flag unsafe direct buy/sell recommendations or guaranteed-return requests as Risky Financial Advice."""


def classify_issue(message: str) -> dict[str, object]:
    fallback = fallback_classification(message)
    service = OpenAIService()
    result = service.generate_structured(
        schema_name="issue_classification",
        schema=ISSUE_CLASSIFICATION_SCHEMA,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Classify this user message:\n\n{message}",
        fallback=fallback,
    )
    return validate_pydantic(IssueClassification, result, fallback)


def fallback_classification(message: str) -> dict[str, object]:
    text = message.lower()

    if is_risky_financial_advice(message):
        return {
            "category": "Risky Financial Advice",
            "urgency": "Medium",
            "requires_human": False,
            "reason": "The user is asking for direct investment advice or guaranteed returns.",
            "suggested_next_step": "Respond with a safety disclaimer and offer educational risk information instead.",
        }

    category = "General Education"
    if any(word in text for word in ["kyc", "pan", "verification", "rejected"]):
        category = "KYC"
    elif "sip" in text:
        category = "SIP"
    elif any(word in text for word in ["mutual fund", "redemption", "nav"]):
        category = "Mutual Funds"
    elif any(word in text for word in ["stock", "share", "equity"]):
        category = "Stocks"
    elif "ipo" in text:
        category = "IPO"
    elif any(word in text for word in ["payment", "debit", "debited", "refund", "bank", "money"]):
        category = "Payments"
    elif any(word in text for word in ["order", "pending", "executed", "execution"]):
        category = "Orders"
    elif any(word in text for word in ["login", "locked", "otp", "account", "password"]):
        category = "Account"

    high_signals = [
        "money debited",
        "debited",
        "account locked",
        "locked",
        "rejected repeatedly",
        "order execution",
        "legal",
        "complaint",
        "angry",
        "frustrated",
        "not acceptable",
        "fraud",
        "unauthorized",
    ]
    urgency = "High" if any(signal in text for signal in high_signals) else "Medium"
    if category == "General Education":
        urgency = "Low"

    requires_human = urgency == "High" or category in {"KYC", "Payments", "Orders", "Account"}
    reason = f"The message appears related to {category.lower()}."
    if requires_human:
        reason += " It may involve money movement, identity checks, account access, or order execution."

    return {
        "category": category,
        "urgency": urgency,
        "requires_human": requires_human,
        "reason": reason,
        "suggested_next_step": _next_step(category, requires_human),
    }


def _next_step(category: str, requires_human: bool) -> str:
    if requires_human:
        return "Collect transaction IDs, timestamps, account details, and route to a human support agent."
    if category == "General Education":
        return "Provide a simple educational explanation with a financial advice disclaimer when relevant."
    return "Share the relevant help-center guidance and monitor whether the user needs escalation."
