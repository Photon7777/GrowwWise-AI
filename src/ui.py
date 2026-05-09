from __future__ import annotations

from html import escape

import streamlit as st


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --gw-green: #00a86b;
            --gw-green-dark: #027a48;
            --gw-green-soft: #ecfdf3;
            --gw-ink: #101828;
            --gw-muted: #667085;
            --gw-border: #e4e7ec;
            --gw-bg: #f8faf9;
            --gw-card: #ffffff;
            --gw-red: #d92d20;
            --gw-orange: #dc6803;
            --gw-yellow-soft: #fffaeb;
            --gw-red-soft: #fef3f2;
            --gw-blue-soft: #eff8ff;
            --gw-shadow: 0 10px 28px rgba(16, 24, 40, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(0, 168, 107, 0.08), transparent 28rem),
                linear-gradient(180deg, #ffffff 0%, var(--gw-bg) 42%, #ffffff 100%);
            color: var(--gw-ink);
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
        }

        header[data-testid="stHeader"] * {
            display: none !important;
        }

        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }

        div[data-testid="stExpander"] > details {
            background: #ffffff !important;
            border: 1px solid var(--gw-border) !important;
            border-radius: 1rem !important;
            box-shadow: 0 6px 18px rgba(16, 24, 40, 0.05);
            overflow: hidden;
        }

        div[data-testid="stExpander"] summary {
            background: #ffffff !important;
            color: var(--gw-ink) !important;
            border-radius: 1rem !important;
        }

        div[data-testid="stExpander"] summary p {
            color: var(--gw-ink) !important;
            font-weight: 800;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        input,
        textarea {
            background-color: #ffffff !important;
            color: var(--gw-ink) !important;
            border-color: #d0d5dd !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="input"] span,
        input::placeholder,
        textarea::placeholder {
            color: var(--gw-muted) !important;
        }

        div[data-baseweb="tag"] {
            background-color: var(--gw-green-soft) !important;
            border: 1px solid #abefc6 !important;
            color: var(--gw-green-dark) !important;
            border-radius: 0.6rem !important;
        }

        div[data-baseweb="tag"] span {
            color: var(--gw-green-dark) !important;
            font-weight: 750 !important;
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--gw-border);
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label {
            color: var(--gw-ink);
        }

        div[data-testid="stButton"] > button {
            border-radius: 0.75rem;
            border: 1px solid rgba(0, 168, 107, 0.24);
            box-shadow: 0 4px 12px rgba(0, 168, 107, 0.12);
            font-weight: 700;
        }

        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, var(--gw-green), #12b76a);
            border: 0;
            color: #ffffff;
        }

        .hero-card {
            background: linear-gradient(135deg, #ffffff 0%, #f3fff8 100%);
            border: 1px solid rgba(0, 168, 107, 0.18);
            border-radius: 1.25rem;
            box-shadow: var(--gw-shadow);
            padding: 1.35rem 1.45rem;
            margin-bottom: 1.1rem;
        }

        .hero-brand {
            color: var(--gw-green-dark);
            font-size: 0.95rem;
            font-weight: 800;
            letter-spacing: 0;
            margin-bottom: 0.35rem;
        }

        .hero-title {
            color: var(--gw-ink);
            font-size: 1.8rem;
            line-height: 1.2;
            font-weight: 850;
            margin: 0;
        }

        .hero-subtitle {
            color: var(--gw-muted);
            font-size: 1rem;
            margin-top: 0.5rem;
            max-width: 820px;
        }

        .section-card,
        .result-card,
        .insight-card,
        .feature-card,
        .chart-card,
        .data-table-container {
            background: var(--gw-card);
            border: 1px solid var(--gw-border);
            border-radius: 1rem;
            box-shadow: 0 6px 18px rgba(16, 24, 40, 0.06);
            padding: 1rem;
            margin: 0.75rem 0;
        }

        .feature-card {
            min-height: 100%;
        }

        .card-title {
            color: var(--gw-ink);
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.4rem;
        }

        .card-body,
        .small-muted {
            color: var(--gw-muted);
            font-size: 0.95rem;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid var(--gw-border);
            border-radius: 1rem;
            box-shadow: 0 8px 20px rgba(16, 24, 40, 0.06);
            padding: 1rem;
            min-height: 118px;
        }

        .kpi-icon {
            font-size: 1.25rem;
            margin-bottom: 0.35rem;
        }

        .kpi-label {
            color: var(--gw-muted);
            font-size: 0.82rem;
            font-weight: 750;
        }

        .kpi-value {
            color: var(--gw-ink);
            font-size: 1.55rem;
            font-weight: 850;
            margin-top: 0.25rem;
        }

        .kpi-helper {
            color: var(--gw-muted);
            font-size: 0.78rem;
            margin-top: 0.28rem;
        }

        .disclaimer-card {
            background: var(--gw-green-soft);
            border: 1px solid rgba(0, 168, 107, 0.20);
            border-left: 5px solid var(--gw-green);
            border-radius: 0.9rem;
            color: #064e3b;
            padding: 0.9rem 1rem;
            margin: 0.75rem 0;
        }

        .warning-card {
            background: var(--gw-yellow-soft);
            border: 1px solid #fedf89;
            border-left: 5px solid var(--gw-orange);
            border-radius: 0.9rem;
            color: #7a2e0e;
            padding: 0.9rem 1rem;
            margin: 0.75rem 0;
        }

        .success-card {
            background: var(--gw-green-soft);
            border: 1px solid rgba(0, 168, 107, 0.22);
            border-radius: 0.9rem;
            color: #05603a;
            font-weight: 700;
            padding: 0.75rem 0.9rem;
            margin: 0.6rem 0;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.25rem 0.65rem;
            font-size: 0.78rem;
            font-weight: 800;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .priority-high {
            color: var(--gw-red);
            background: var(--gw-red-soft);
            border-color: #fecdca;
        }

        .priority-medium {
            color: var(--gw-orange);
            background: var(--gw-yellow-soft);
            border-color: #fedf89;
        }

        .priority-low {
            color: var(--gw-green-dark);
            background: var(--gw-green-soft);
            border-color: #abefc6;
        }

        .status-neutral {
            color: #175cd3;
            background: var(--gw-blue-soft);
            border-color: #b2ddff;
        }

        .sidebar-brand {
            padding: 0.75rem 0 0.35rem 0;
        }

        .sidebar-title {
            font-size: 1.25rem;
            font-weight: 850;
            color: var(--gw-ink);
            margin-bottom: 0.2rem;
        }

        .sidebar-subtitle {
            color: var(--gw-muted);
            font-size: 0.88rem;
            line-height: 1.35;
        }

        .sidebar-footer {
            color: var(--gw-muted);
            font-size: 0.8rem;
            padding-top: 1rem;
        }

        .example-list {
            margin: 0.35rem 0 0 0;
            padding-left: 1.1rem;
            color: var(--gw-muted);
        }

        .example-list li {
            margin: 0.3rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-brand">📈 GrowwWise AI</div>
            <h1 class="hero-title">{escape(title)}</h1>
            <div class="hero-subtitle">{escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(icon: str, label: str, value: str, helper_text: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{escape(icon)}</div>
            <div class="kpi-label">{escape(label)}</div>
            <div class="kpi-value">{escape(value)}</div>
            <div class="kpi-helper">{escape(helper_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_card(title: str, content: str) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if content:
            st.markdown(content)


def render_disclaimer(text: str) -> None:
    st.markdown(
        f'<div class="disclaimer-card">🛡️ {escape(text)}</div>',
        unsafe_allow_html=True,
    )


def status_badge(label: str, status_type: str) -> str:
    class_name = {
        "high": "priority-high",
        "medium": "priority-medium",
        "low": "priority-low",
        "success": "priority-low",
        "warning": "priority-medium",
        "danger": "priority-high",
        "neutral": "status-neutral",
    }.get(status_type.lower(), "status-neutral")
    return f'<span class="status-badge {class_name}">{escape(label)}</span>'


def render_status_badge(label: str, status_type: str) -> None:
    st.markdown(status_badge(label, status_type), unsafe_allow_html=True)


def render_example_card(title: str, examples: list[str]) -> None:
    items = "".join(f"<li>{escape(example)}</li>" for example in examples)
    st.markdown(
        f"""
        <div class="feature-card">
            <div class="card-title">{escape(title)}</div>
            <ul class="example-list">{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_success_message(text: str) -> None:
    st.markdown(f'<div class="success-card">✅ {escape(text)}</div>', unsafe_allow_html=True)


def render_warning_message(text: str) -> None:
    st.markdown(f'<div class="warning-card">⚠️ {escape(text)}</div>', unsafe_allow_html=True)
