from __future__ import annotations

import re


SAFE_FINANCIAL_RESPONSE = (
    "I can help explain investing concepts and risks, but I cannot provide "
    "guaranteed-return claims or direct buy/sell recommendations. This is for "
    "educational purposes and not financial advice."
)


RISKY_PATTERNS = [
    r"\bwhich stock should i buy\b",
    r"\bwhat stock should i buy\b",
    r"\bshould i buy\b.*\b(stock|share|option|future|f&o)\b",
    r"\bshould i sell\b.*\b(stock|share|option|future|f&o)\b",
    r"\bbuy today\b",
    r"\bsell today\b",
    r"\brecommend (a )?(stock|share|trade)\b",
    r"\bguaranteed returns?\b",
    r"\bguarantee\b.*\bprofit|return\b",
    r"\brisk[- ]?free profit\b",
    r"\brisk[- ]?free returns?\b",
    r"\bmake risk[- ]?free\b",
    r"\bdouble (my )?(money|investment)\b",
    r"\bstock that will double\b",
    r"\bmultibagger\b",
    r"\bsure[- ]?shot\b",
    r"\bput all my money\b.*\b(f&o|options|futures|stock|crypto)\b",
    r"\ball in\b.*\b(f&o|options|futures|stock|crypto)\b",
]


def is_risky_financial_advice(prompt: str) -> bool:
    text = prompt.lower().strip()
    return any(re.search(pattern, text) for pattern in RISKY_PATTERNS)


def safe_financial_response() -> str:
    return SAFE_FINANCIAL_RESPONSE
