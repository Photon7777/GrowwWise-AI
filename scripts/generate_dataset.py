from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import random

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = BASE_DIR / "data" / "support_tickets.csv"


CITY_STATE = [
    ("Bengaluru", "Karnataka"),
    ("Mumbai", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Hyderabad", "Telangana"),
    ("Pune", "Maharashtra"),
    ("Chennai", "Tamil Nadu"),
    ("Kolkata", "West Bengal"),
    ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"),
    ("Gurugram", "Haryana"),
]


ISSUES = [
    {
        "category": "Payments",
        "subcategory": "Money Debited Investment Not Confirmed",
        "weight": 50,
        "escalation_rate": 0.62,
        "base_hours": 32,
        "messages": [
            "Money was debited from my bank but the investment is still not confirmed.",
            "Payment completed from my bank account but the transaction status is pending.",
            "Amount got deducted and I cannot see the mutual fund order confirmation.",
        ],
    },
    {
        "category": "SIP",
        "subcategory": "SIP Payment Failed",
        "weight": 48,
        "escalation_rate": 0.48,
        "base_hours": 22,
        "messages": [
            "My SIP failed but money got debited from my bank account.",
            "SIP autopay failed twice and the app still shows payment pending.",
            "The SIP installment did not go through even though my bank shows a debit.",
        ],
    },
    {
        "category": "KYC",
        "subcategory": "KYC Rejected",
        "weight": 42,
        "escalation_rate": 0.55,
        "base_hours": 38,
        "messages": [
            "My KYC was rejected even though I uploaded PAN and address proof.",
            "KYC keeps failing and I do not understand the rejection reason.",
            "The app says my selfie or document verification failed during KYC.",
        ],
    },
    {
        "category": "Orders",
        "subcategory": "Stock Order Pending",
        "weight": 36,
        "escalation_rate": 0.46,
        "base_hours": 18,
        "messages": [
            "My stock order is still pending and funds are blocked.",
            "The order did not execute even though the market price reached my limit.",
            "Stock order status is stuck and I need to know if it was sent to the exchange.",
        ],
    },
    {
        "category": "Stocks",
        "subcategory": "Stock Holdings Not Visible",
        "weight": 22,
        "escalation_rate": 0.24,
        "base_hours": 14,
        "messages": [
            "My bought shares are not visible in holdings after the order was completed.",
            "The stock is showing in positions but not in my holdings section.",
            "My portfolio value looks incorrect after a stock transaction.",
        ],
    },
    {
        "category": "IPO",
        "subcategory": "IPO Mandate Failed",
        "weight": 24,
        "escalation_rate": 0.34,
        "base_hours": 20,
        "messages": [
            "My IPO UPI mandate failed and the bid is not confirmed.",
            "I approved the IPO mandate but the application still says pending.",
            "IPO amount is blocked but I cannot see the application status clearly.",
        ],
    },
    {
        "category": "Account",
        "subcategory": "Login Issue",
        "weight": 30,
        "escalation_rate": 0.30,
        "base_hours": 12,
        "messages": [
            "I am not receiving OTP and cannot log in to my account.",
            "Login is failing after I changed my phone and reinstalled the app.",
            "The app keeps asking for OTP but does not let me access my account.",
        ],
    },
    {
        "category": "Account",
        "subcategory": "Account Locked",
        "weight": 22,
        "escalation_rate": 0.65,
        "base_hours": 26,
        "messages": [
            "My account is locked and I need urgent help to access my holdings.",
            "The app says my account is temporarily blocked after OTP attempts.",
            "I cannot access my account and I am worried about unauthorized activity.",
        ],
    },
    {
        "category": "Mutual Funds",
        "subcategory": "Redemption Delay",
        "weight": 28,
        "escalation_rate": 0.28,
        "base_hours": 30,
        "messages": [
            "My mutual fund redemption is delayed and money is not credited yet.",
            "I redeemed my fund but the bank credit has not arrived after the expected date.",
            "Redemption status is processed but I cannot see the money in my bank account.",
        ],
    },
    {
        "category": "Risky Financial Advice",
        "subcategory": "F&O Risk Query",
        "weight": 16,
        "escalation_rate": 0.08,
        "base_hours": 8,
        "messages": [
            "Can I put all my money into F&O for quick profit?",
            "Is there a safe options strategy that gives guaranteed returns?",
            "Please explain why F&O is considered risky for beginners.",
        ],
    },
    {
        "category": "General Education",
        "subcategory": "ETF vs Mutual Fund",
        "weight": 18,
        "escalation_rate": 0.04,
        "base_hours": 6,
        "messages": [
            "What is the difference between an ETF and a mutual fund?",
            "Should beginners understand ETFs differently from mutual funds?",
            "I want to learn how ETFs trade compared with mutual funds.",
        ],
    },
    {
        "category": "Mutual Funds",
        "subcategory": "NAV Explanation",
        "weight": 18,
        "escalation_rate": 0.08,
        "base_hours": 7,
        "messages": [
            "Why is my mutual fund NAV different from yesterday?",
            "Please explain when NAV is calculated for mutual fund orders.",
            "I invested today but the NAV date looks different in the app.",
        ],
    },
    {
        "category": "IPO",
        "subcategory": "IPO Application Status",
        "weight": 18,
        "escalation_rate": 0.12,
        "base_hours": 10,
        "messages": [
            "When will I know my IPO allotment status?",
            "My IPO application is submitted but I cannot see the allotment result.",
            "The IPO bid is visible but the final status is still pending.",
        ],
    },
]


CHANNELS = ["Chat", "Email", "Phone", "In-App"]
CUSTOMER_SEGMENTS = [
    "New Investor",
    "Active Trader",
    "Mutual Fund Investor",
    "Long-Term Investor",
    "High Value Customer",
]
APP_VERSIONS = ["8.21.0", "8.22.1", "8.23.0", "8.24.2", "8.25.0"]


def weighted_choice(items: list[dict]) -> dict:
    weights = [item["weight"] for item in items]
    return random.choices(items, weights=weights, k=1)[0]


def choose_status(escalated: bool) -> str:
    if escalated:
        return random.choices(
            ["Escalated", "Resolved", "In Progress", "Open"],
            weights=[0.34, 0.34, 0.20, 0.12],
            k=1,
        )[0]
    return random.choices(
        ["Resolved", "In Progress", "Open", "Escalated"],
        weights=[0.68, 0.18, 0.12, 0.02],
        k=1,
    )[0]


def choose_urgency(issue: dict, escalated: bool) -> str:
    high_signal = issue["subcategory"] in {
        "Money Debited Investment Not Confirmed",
        "SIP Payment Failed",
        "KYC Rejected",
        "Stock Order Pending",
        "Account Locked",
        "IPO Mandate Failed",
    }
    if high_signal or escalated:
        return random.choices(["High", "Medium", "Low"], weights=[0.58, 0.34, 0.08], k=1)[0]
    return random.choices(["Low", "Medium", "High"], weights=[0.50, 0.38, 0.12], k=1)[0]


def choose_priority(urgency: str, status: str) -> str:
    if urgency == "High" or status == "Escalated":
        return random.choices(["High", "Medium", "Low"], weights=[0.70, 0.25, 0.05], k=1)[0]
    if urgency == "Medium":
        return random.choices(["Medium", "High", "Low"], weights=[0.62, 0.20, 0.18], k=1)[0]
    return random.choices(["Low", "Medium", "High"], weights=[0.70, 0.25, 0.05], k=1)[0]


def choose_sentiment(status: str, priority: str, category: str) -> str:
    if status == "Escalated" or priority == "High":
        return random.choices(["Frustrated", "Angry", "Confused", "Calm"], weights=[0.50, 0.20, 0.22, 0.08], k=1)[0]
    if category in {"KYC", "Payments", "SIP"}:
        return random.choices(["Confused", "Frustrated", "Calm", "Angry"], weights=[0.38, 0.34, 0.22, 0.06], k=1)[0]
    return random.choices(["Calm", "Confused", "Frustrated", "Angry"], weights=[0.48, 0.34, 0.15, 0.03], k=1)[0]


def resolution_time(issue: dict, status: str, priority: str) -> float:
    noise = np.random.lognormal(mean=0.0, sigma=0.45)
    multiplier = 1.0
    if status == "Escalated":
        multiplier += random.uniform(0.55, 1.15)
    elif status == "Open":
        multiplier += random.uniform(0.15, 0.65)
    elif status == "In Progress":
        multiplier += random.uniform(0.25, 0.85)
    if priority == "High":
        multiplier += 0.20
    return round(float(np.clip(issue["base_hours"] * noise * multiplier, 1.0, 120.0)), 1)


def csat_score(category: str, status: str, escalated: bool, priority: str) -> float:
    score = random.normalvariate(4.25, 0.55)
    if category in {"KYC", "Payments", "Orders", "SIP"}:
        score -= 0.35
    if status == "Escalated":
        score -= 0.90
    elif status in {"Open", "In Progress"}:
        score -= 0.55
    if escalated:
        score -= 0.30
    if priority == "High":
        score -= 0.20
    return round(float(np.clip(score, 1.0, 5.0)), 1)


def generate_dataset(row_count: int = 420) -> pd.DataFrame:
    random.seed(42)
    np.random.seed(42)

    today = date.today()
    rows = []

    for index in range(row_count):
        issue = weighted_choice(ISSUES)
        created = today - timedelta(days=random.randint(0, 89))
        city, state = random.choice(CITY_STATE)
        escalated = random.random() < issue["escalation_rate"]
        status = choose_status(escalated)
        urgency = choose_urgency(issue, escalated)
        priority = choose_priority(urgency, status)
        sentiment = choose_sentiment(status, priority, issue["category"])
        hours = resolution_time(issue, status, priority)
        csat = csat_score(issue["category"], status, escalated, priority)

        rows.append(
            {
                "ticket_id": f"TKT-{today.strftime('%Y%m')}-{index + 1:04d}",
                "created_date": created.isoformat(),
                "user_id": f"USR-{random.randint(100000, 999999)}",
                "issue_category": issue["category"],
                "issue_subcategory": issue["subcategory"],
                "user_message": random.choice(issue["messages"]),
                "urgency": urgency,
                "priority": priority,
                "sentiment": sentiment,
                "status": status,
                "resolution_time_hours": hours,
                "channel": random.choices(CHANNELS, weights=[0.42, 0.22, 0.16, 0.20], k=1)[0],
                "city": city,
                "state": state,
                "app_version": random.choices(APP_VERSIONS, weights=[0.12, 0.16, 0.25, 0.28, 0.19], k=1)[0],
                "customer_segment": random.choices(
                    CUSTOMER_SEGMENTS,
                    weights=[0.28, 0.19, 0.24, 0.20, 0.09],
                    k=1,
                )[0],
                "human_escalation_required": escalated,
                "csat_score": csat,
            }
        )

    return pd.DataFrame(rows).sort_values("created_date").reset_index(drop=True)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate_dataset()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Generated {len(df)} rows at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
