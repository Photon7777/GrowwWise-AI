from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from src.classifier import classify_issue
from src.openai_client import OpenAIService
from src.utils import validate_pydantic


class TicketSummary(BaseModel):
    summary: str
    issue_type: str
    priority: Literal["Low", "Medium", "High"]
    sentiment: Literal["Calm", "Confused", "Frustrated", "Angry"]
    suggested_action: str
    human_escalation_required: bool


TICKET_SUMMARY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "issue_type": {"type": "string"},
        "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
        "sentiment": {"type": "string", "enum": ["Calm", "Confused", "Frustrated", "Angry"]},
        "suggested_action": {"type": "string"},
        "human_escalation_required": {"type": "boolean"},
    },
    "required": [
        "summary",
        "issue_type",
        "priority",
        "sentiment",
        "suggested_action",
        "human_escalation_required",
    ],
}


SYSTEM_PROMPT = """Summarize fintech support complaints for a human support dashboard.
Return only structured JSON matching the schema.
Keep summaries short, operational, and useful for support agents.
Escalate payment failures, account locks, KYC rejection, order execution issues, legal/compliance issues, and angry users."""


def summarize_ticket(complaint: str) -> dict[str, object]:
    fallback = fallback_ticket_summary(complaint)
    service = OpenAIService()
    result = service.generate_structured(
        schema_name="support_ticket_summary",
        schema=TICKET_SUMMARY_SCHEMA,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Summarize this support complaint:\n\n{complaint}",
        fallback=fallback,
    )
    return validate_pydantic(TicketSummary, result, fallback)


def fallback_ticket_summary(complaint: str) -> dict[str, object]:
    classification = classify_issue(complaint)
    text = complaint.lower()

    sentiment: Literal["Calm", "Confused", "Frustrated", "Angry"] = "Calm"
    if any(word in text for word in ["angry", "furious", "scam", "legal", "complaint"]):
        sentiment = "Angry"
    elif any(word in text for word in ["failed", "twice", "again", "frustrated", "not acceptable", "still"]):
        sentiment = "Frustrated"
    elif any(word in text for word in ["why", "confused", "not sure", "pending"]):
        sentiment = "Confused"

    category = str(classification["category"])
    issue_type = "General Support"
    if category == "SIP":
        issue_type = "SIP Payment Failure"
    elif category == "Payments":
        issue_type = "Payment or Refund Issue"
    elif category == "KYC":
        issue_type = "KYC Verification Issue"
    elif category == "Orders":
        issue_type = "Order Status Issue"
    elif category == "Account":
        issue_type = "Account Access Issue"
    elif category == "IPO":
        issue_type = "IPO Application Issue"
    elif category == "Mutual Funds":
        issue_type = "Mutual Fund Service Issue"

    return {
        "summary": _short_summary(complaint, issue_type),
        "issue_type": issue_type,
        "priority": classification["urgency"],
        "sentiment": sentiment,
        "suggested_action": _suggested_action(issue_type),
        "human_escalation_required": bool(classification["requires_human"]),
    }


def _short_summary(complaint: str, issue_type: str) -> str:
    cleaned = " ".join(complaint.strip().split())
    if len(cleaned) > 130:
        cleaned = cleaned[:127].rstrip() + "..."
    return f"User reports {issue_type.lower()}: {cleaned}"


def _suggested_action(issue_type: str) -> str:
    actions = {
        "SIP Payment Failure": "Check SIP mandate, payment gateway status, debit confirmation, and refund or retry timeline.",
        "Payment or Refund Issue": "Verify bank reference, transaction status, reconciliation state, and refund timeline.",
        "KYC Verification Issue": "Review PAN details, document clarity, rejection reason, and compliance escalation path.",
        "Order Status Issue": "Check exchange order status, blocked funds or holdings, order type, and execution logs.",
        "Account Access Issue": "Verify registered phone number, OTP attempts, device changes, and security lock status.",
        "IPO Application Issue": "Check UPI mandate status, bid confirmation, blocked funds, and registrar timeline.",
    }
    return actions.get(issue_type, "Review user context and provide help-center guidance or escalation as needed.")
