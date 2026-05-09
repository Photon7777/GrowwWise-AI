from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import (
    answer_dataset_question,
    calculate_kpis,
    filter_support_tickets,
    generate_business_insights,
    load_support_tickets,
)
from src.classifier import classify_issue
from src.guardrails import is_risky_financial_advice, safe_financial_response
from src.openai_client import OpenAIService
from src.portfolio_analyzer import analyze_portfolio, calculate_portfolio_metrics, load_portfolio
from src.rag import RAGAssistant
from src.ticket_summary import summarize_ticket
from src.ui import (
    inject_custom_css,
    render_disclaimer,
    render_example_card,
    render_header,
    render_kpi_card,
    render_result_card,
    render_status_badge,
    render_success_message,
    render_warning_message,
    status_badge,
)
from src.utils import format_currency, format_percent


st.set_page_config(
    page_title="GrowwWise AI",
    page_icon="📈",
    layout="wide",
)
inject_custom_css()


@st.cache_resource(show_spinner=False)
def get_rag_assistant() -> RAGAssistant:
    return RAGAssistant()


@st.cache_data(show_spinner=False)
def get_support_tickets_data() -> pd.DataFrame:
    return load_support_tickets()


def render_sidebar() -> str:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-title">📈 GrowwWise AI</div>
            <div class="sidebar-subtitle">AI-powered support intelligence for retail investors</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section = st.sidebar.radio(
        "Navigation",
        [
            "Ask Assistant",
            "Issue Classification",
            "Portfolio Risk Explainer",
            "Support Ticket Summary",
            "Analytics Dashboard",
        ],
    )

    st.sidebar.divider()
    service = OpenAIService()
    if service.enabled:
        st.sidebar.success(f"Live OpenAI mode: {service.chat_model}")
    else:
        st.sidebar.markdown(
            '<div class="warning-card">OpenAI API key not found. Running in demo fallback mode.</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.info("Demo Mode uses mock help docs, a synthetic support dataset, and safe financial guardrails.")
    st.sidebar.markdown(
        '<div class="sidebar-footer">Built with OpenAI, RAG, ChromaDB, Pandas, Plotly, and Streamlit.</div>',
        unsafe_allow_html=True,
    )
    return section


def render_exception(message: str, exc: Exception) -> None:
    render_warning_message(message)
    with st.expander("Technical details"):
        st.exception(exc)


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander("Retrieved support references"):
        for index, source in enumerate(sources, start=1):
            metadata = source["metadata"]
            st.markdown(f"**{index}. {metadata['title']}**")
            st.caption(f"Category: {metadata['category']} | Source ID: {metadata['source_id']}")
            st.write(source["content"].split("\n", maxsplit=2)[-1])


def render_value_card(title: str, value: str, badge_type: str | None = None, helper: str | None = None) -> None:
    value_html = status_badge(value, badge_type) if badge_type else f"<strong>{escape(value)}</strong>"
    helper_html = f'<div class="card-body">{escape(helper)}</div>' if helper else ""
    st.markdown(
        f"""
        <div class="result-card">
            <div class="card-title">{escape(title)}</div>
            <div>{value_html}</div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart(title: str, fig, show_legend: bool = True) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        fig.update_layout(
            height=340,
            margin=dict(l=20, r=20, t=24, b=20),
            showlegend=show_legend,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)


def ask_assistant_section() -> None:
    render_header(
        "🤖 Ask Assistant",
        "Ask support and investing education questions. GrowwWise AI retrieves help-center context, applies guardrails, and generates a grounded response.",
    )
    render_disclaimer("Investment-related explanations are educational only and are not financial advice.")

    prompt_examples = [
        "My SIP failed but money got debited. What should I do?",
        "Why is my stock order still pending?",
        "What is the difference between ETF and mutual fund?",
    ]
    render_example_card("Try these support questions", prompt_examples)

    selected = st.selectbox("Choose an example", [""] + prompt_examples + ["Why was my KYC rejected?"])
    question = st.text_area(
        "Your question",
        value=selected,
        height=120,
        placeholder="Example: My SIP failed twice but money got debited from my bank account.",
    )

    if st.button("Ask GrowwWise AI", type="primary"):
        if not question.strip():
            render_warning_message("Enter a support or education question first.")
            return

        try:
            if is_risky_financial_advice(question):
                result = {
                    "answer": safe_financial_response(),
                    "sources": [],
                    "guardrail_triggered": True,
                }
            else:
                assistant = get_rag_assistant()
                with st.spinner("Searching support knowledge base..."):
                    sources = assistant.retrieve(question.strip())
                with st.spinner("Generating grounded answer with OpenAI..."):
                    result = assistant.answer_from_sources(question.strip(), sources)

            render_success_message("Answer generated successfully")
            if result["guardrail_triggered"]:
                render_warning_message("Financial safety guardrail triggered.")
            render_result_card("GrowwWise AI Answer", result["answer"])
            render_sources(result["sources"])
        except Exception as exc:
            render_exception("I could not generate an answer. Please try again or use demo fallback mode.", exc)


def classification_section() -> None:
    render_header(
        "🧭 Issue Classification",
        "Classify incoming support messages by category, urgency, escalation need, reason, and next best action.",
    )

    examples = [
        "My KYC keeps getting rejected even after uploading documents.",
        "My IPO mandate failed but money is blocked.",
        "I cannot login to my account.",
    ]
    render_example_card("Example messages", examples)

    default = "My SIP failed twice but money got debited from my bank account. It still says payment pending."
    message = st.text_area("User message", value=default, height=140)

    if st.button("Classify Issue", type="primary"):
        if not message.strip():
            render_warning_message("Enter a support message first.")
            return

        try:
            with st.spinner("Classifying issue and estimating urgency..."):
                result = classify_issue(message.strip())
            render_success_message("Issue classified successfully")

            urgency = str(result["urgency"])
            human_required = bool(result["requires_human"])
            cols = st.columns(3)
            with cols[0]:
                render_value_card("Category", str(result["category"]), "neutral")
            with cols[1]:
                render_value_card("Urgency", urgency, urgency.lower())
            with cols[2]:
                render_value_card(
                    "Human Escalation",
                    "Required" if human_required else "Not required",
                    "danger" if human_required else "success",
                )

            detail_cols = st.columns(2)
            with detail_cols[0]:
                render_result_card("Reason", str(result["reason"]))
            with detail_cols[1]:
                render_result_card("Suggested Next Step", str(result["suggested_next_step"]))

            with st.expander("Structured JSON"):
                st.json(result)
        except Exception as exc:
            render_exception("I could not classify this issue. Please try a shorter support message.", exc)


def portfolio_section() -> None:
    render_header(
        "💼 Portfolio Risk Explainer",
        "Analyze a mock retail investor portfolio with Pandas, then generate a plain-English risk explanation with financial safety guardrails.",
    )
    render_disclaimer("This module uses mock holdings and provides educational risk explanation only.")

    df = load_portfolio()
    metrics = calculate_portfolio_metrics(df)
    render_example_card(
        "Sample portfolio module",
        [
            "Uses mock holdings from data/sample_portfolio.csv.",
            "Calculates allocation by asset, asset type, and risk level.",
            "Generates an educational explanation without buy or sell recommendations.",
        ],
    )

    cols = st.columns(3)
    with cols[0]:
        render_kpi_card("💰", "Total Portfolio Value", format_currency(metrics["total_value"]), "Mock portfolio value")
    with cols[1]:
        render_kpi_card(
            "⚠️",
            "High-Risk Exposure",
            format_percent(float(metrics["risk_allocations"].get("High", 0.0))),
            "Share marked High risk",
        )
    largest_asset = max(metrics["asset_allocations"].items(), key=lambda item: item[1])
    with cols[2]:
        render_kpi_card(
            "📌",
            "Largest Holding",
            largest_asset[0],
            f"{format_percent(float(largest_asset[1]))} of portfolio",
        )

    with st.container(border=True):
        st.markdown("**Sample Portfolio Preview**")
        st.dataframe(df, width="stretch", hide_index=True)

    chart_cols = st.columns(2)
    with chart_cols[0]:
        risk_frame = pd.DataFrame(
            [{"risk_level": key, "allocation": value} for key, value in metrics["risk_allocations"].items()]
        )
        render_chart(
            "Risk Distribution",
            px.pie(risk_frame, names="risk_level", values="allocation", hole=0.42),
        )
    with chart_cols[1]:
        asset_frame = pd.DataFrame(
            [{"asset_name": key, "allocation": value} for key, value in metrics["asset_allocations"].items()]
        ).sort_values("allocation", ascending=False)
        render_chart(
            "Asset Distribution",
            px.bar(
                asset_frame,
                x="asset_name",
                y="allocation",
                color="asset_name",
                labels={"asset_name": "Asset", "allocation": "Allocation (%)"},
            ),
            show_legend=False,
        )

    if st.button("Generate Portfolio Risk Explanation", type="primary"):
        try:
            with st.spinner("Analyzing portfolio allocation and risk..."):
                result = analyze_portfolio()
            render_success_message("Portfolio analysis complete")
            render_result_card("AI Risk Explanation", result["explanation"])
            render_disclaimer("This is for educational purposes and not financial advice.")
        except Exception as exc:
            render_exception("I could not analyze the portfolio. Please check the sample CSV file.", exc)


def ticket_summary_section() -> None:
    render_header(
        "🎫 Support Ticket Summary",
        "Turn raw customer complaints into support-agent summaries with priority, sentiment, escalation need, and suggested action.",
    )

    render_example_card(
        "Example complaint",
        ["My SIP failed twice and money got debited both times. I am very frustrated."],
    )

    default = "My SIP failed twice but money got debited from my bank account. It still says payment pending."
    complaint = st.text_area("Customer complaint", value=default, height=150)

    if st.button("Summarize Ticket", type="primary"):
        if not complaint.strip():
            render_warning_message("Enter a complaint first.")
            return

        try:
            with st.spinner("Summarizing support ticket..."):
                result = summarize_ticket(complaint.strip())
            render_success_message("Ticket summary created")

            priority = str(result["priority"])
            escalation_required = bool(result["human_escalation_required"])
            cols = st.columns(4)
            with cols[0]:
                render_value_card("Issue Type", str(result["issue_type"]), "neutral")
            with cols[1]:
                render_value_card("Priority", priority, priority.lower())
            with cols[2]:
                sentiment_type = "danger" if result["sentiment"] == "Angry" else "warning" if result["sentiment"] == "Frustrated" else "neutral"
                render_value_card("Sentiment", str(result["sentiment"]), sentiment_type)
            with cols[3]:
                render_value_card(
                    "Human Escalation",
                    "Required" if escalation_required else "Not required",
                    "danger" if escalation_required else "success",
                )

            detail_cols = st.columns(2)
            with detail_cols[0]:
                render_result_card("Summary", str(result["summary"]))
            with detail_cols[1]:
                render_result_card("Suggested Action", str(result["suggested_action"]))

            with st.expander("Structured JSON"):
                st.json(result)
        except Exception as exc:
            render_exception("I could not summarize this support ticket. Please try again.", exc)


def analytics_dashboard_section() -> None:
    render_header(
        "📈 Analytics Dashboard",
        "Stakeholder-ready support analytics for ticket trends, escalation drivers, resolution bottlenecks, CSAT patterns, and AI business insights.",
    )

    try:
        df = get_support_tickets_data()
    except Exception as exc:
        render_exception("I could not load or generate the support ticket dataset.", exc)
        return

    min_date = df["created_date"].min().date()
    max_date = df["created_date"].max().date()

    with st.expander("Dashboard Filters", expanded=True):
        filter_cols = st.columns(3)
        with filter_cols[0]:
            date_range = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            categories = st.multiselect(
                "Issue category",
                sorted(df["issue_category"].unique()),
                default=sorted(df["issue_category"].unique()),
            )
        with filter_cols[1]:
            priorities = st.multiselect("Priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
            statuses = st.multiselect("Status", sorted(df["status"].unique()), default=sorted(df["status"].unique()))
        with filter_cols[2]:
            channels = st.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
            customer_segments = st.multiselect(
                "Customer segment",
                sorted(df["customer_segment"].unique()),
                default=sorted(df["customer_segment"].unique()),
            )

    if not isinstance(date_range, tuple) or len(date_range) != 2:
        render_warning_message("Select both a start and end date to load the dashboard.")
        return

    filtered = filter_support_tickets(
        df,
        date_range=date_range,
        categories=categories,
        priorities=priorities,
        statuses=statuses,
        channels=channels,
        customer_segments=customer_segments,
    )

    if filtered.empty:
        render_warning_message("No support tickets match the selected filters.")
        return

    kpis = calculate_kpis(filtered)
    metric_cols = st.columns(6)
    with metric_cols[0]:
        render_kpi_card("📩", "Total Tickets", f"{kpis['total_tickets']:,}", "Filtered support requests")
    with metric_cols[1]:
        render_kpi_card("⏱️", "Avg Resolution", f"{kpis['avg_resolution_time_hours']:.1f}h", "Mean handling time")
    with metric_cols[2]:
        render_kpi_card("🚨", "Escalation Rate", format_percent(float(kpis["human_escalation_rate"])), "Human handoff share")
    with metric_cols[3]:
        render_kpi_card("⭐", "Avg CSAT", f"{kpis['avg_csat_score']:.2f}/5", "Customer rating")
    with metric_cols[4]:
        render_kpi_card("🔥", "High Priority", f"{kpis['high_priority_tickets']:,}", "Needs faster triage")
    with metric_cols[5]:
        render_kpi_card("📬", "Open Tickets", f"{kpis['open_tickets']:,}", "Still unresolved")

    st.markdown("### Ticket Trends")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        volume = (
            filtered.assign(created_day=filtered["created_date"].dt.date)
            .groupby("created_day", as_index=False)["ticket_id"]
            .count()
            .rename(columns={"ticket_id": "tickets"})
        )
        render_chart(
            "Ticket Volume Trend",
            px.line(
                volume,
                x="created_day",
                y="tickets",
                markers=True,
                labels={"created_day": "Date", "tickets": "Tickets"},
            ),
        )

    with chart_cols[1]:
        category_counts = count_frame(filtered, "issue_category", "tickets")
        render_chart(
            "Ticket Categories",
            px.bar(
                category_counts,
                x="issue_category",
                y="tickets",
                color="issue_category",
                labels={"issue_category": "Issue category", "tickets": "Tickets"},
            ),
            show_legend=False,
        )

    chart_cols = st.columns(2)
    with chart_cols[0]:
        priority_counts = count_frame(filtered, "priority", "tickets", order=["High", "Medium", "Low"])
        render_chart(
            "Priority Breakdown",
            px.bar(priority_counts, x="priority", y="tickets", color="priority"),
            show_legend=False,
        )

    with chart_cols[1]:
        sentiment_counts = count_frame(filtered, "sentiment", "tickets", order=["Angry", "Frustrated", "Confused", "Calm"])
        render_chart(
            "Sentiment Distribution",
            px.bar(sentiment_counts, x="sentiment", y="tickets", color="sentiment"),
            show_legend=False,
        )

    st.markdown("### Operational Health")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        resolution = (
            filtered.groupby("issue_category", as_index=False)["resolution_time_hours"]
            .mean()
            .sort_values("resolution_time_hours", ascending=False)
        )
        render_chart(
            "Avg Resolution Time by Category",
            px.bar(
                resolution,
                x="issue_category",
                y="resolution_time_hours",
                color="issue_category",
                labels={"issue_category": "Issue category", "resolution_time_hours": "Avg hours"},
            ),
            show_legend=False,
        )

    with chart_cols[1]:
        csat = (
            filtered.groupby("customer_segment", as_index=False)["csat_score"]
            .mean()
            .sort_values("csat_score")
        )
        fig = px.bar(
            csat,
            x="customer_segment",
            y="csat_score",
            color="customer_segment",
            labels={"customer_segment": "Customer segment", "csat_score": "Avg CSAT"},
        )
        fig.update_yaxes(range=[0, 5])
        render_chart("CSAT by Customer Segment", fig, show_legend=False)

    chart_cols = st.columns(2)
    with chart_cols[0]:
        escalation = (
            filtered.groupby("issue_category", as_index=False)["human_escalation_required"]
            .mean()
            .assign(escalation_rate=lambda data: data["human_escalation_required"] * 100)
            .sort_values("escalation_rate", ascending=False)
        )
        render_chart(
            "Escalation Rate by Category",
            px.bar(
                escalation,
                x="issue_category",
                y="escalation_rate",
                color="issue_category",
                labels={"issue_category": "Issue category", "escalation_rate": "Escalation rate (%)"},
            ),
            show_legend=False,
        )

    with chart_cols[1]:
        channel_counts = count_frame(filtered, "channel", "tickets")
        render_chart(
            "Channel Distribution",
            px.pie(channel_counts, names="channel", values="tickets", hole=0.42),
        )

    st.markdown("### 🧠 AI Insights")
    with st.container(border=True):
        st.markdown("**Generate business insights**")
        st.caption("Uses aggregated dashboard statistics, not raw user data.")
        if not OpenAIService().enabled:
            render_warning_message("OpenAI API key not found. Running deterministic fallback insights.")
        if st.button("Generate AI Business Insights", type="primary"):
            try:
                with st.spinner("Analyzing support trends and generating business insights..."):
                    insights = generate_business_insights(filtered)
                render_success_message("Business insights generated")
                render_result_card("Stakeholder Summary", insights)
            except Exception as exc:
                render_exception("I could not generate business insights from this dashboard view.", exc)

    st.markdown("### Ask Questions About the Dataset")
    render_example_card(
        "Example analytics questions",
        [
            "Which issue category has the highest escalation rate?",
            "Which customer segment has the lowest CSAT?",
            "What should support teams prioritize first?",
        ],
    )
    examples = [
        "Which issue category has the highest resolution time?",
        "Which customer segment has the lowest CSAT?",
        "What are the top 3 reasons users escalate to humans?",
        "Which channels receive the most high-priority tickets?",
        "What should the support team improve first?",
    ]
    selected_question = st.selectbox("Choose an example question", examples)
    custom_question = st.text_input(
        "Ask a business question",
        placeholder="Ask a business question about the filtered support data...",
    )
    question = custom_question.strip() or selected_question

    if st.button("Ask Dataset Question", type="primary"):
        try:
            with st.spinner("Aggregating dataset and generating answer..."):
                answer = answer_dataset_question(question, filtered)
            render_success_message("Dataset answer generated")
            render_result_card("Answer Based on Aggregated Data", answer)
            st.caption("This answer is based on summary statistics from the filtered dataset, not raw user rows.")
        except Exception as exc:
            render_exception("I could not answer this dataset question. Please try another question.", exc)

    with st.expander("Filtered Data Preview"):
        preview = filtered.copy()
        preview["created_date"] = preview["created_date"].dt.date
        st.dataframe(preview.head(80), width="stretch", hide_index=True)


def count_frame(df: pd.DataFrame, column: str, value_name: str, order: list[str] | None = None) -> pd.DataFrame:
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, value_name]
    if order:
        counts[column] = pd.Categorical(counts[column], categories=order, ordered=True)
        counts = counts.sort_values(column)
    return counts


def main() -> None:
    section = render_sidebar()

    if section == "Ask Assistant":
        ask_assistant_section()
    elif section == "Issue Classification":
        classification_section()
    elif section == "Portfolio Risk Explainer":
        portfolio_section()
    elif section == "Support Ticket Summary":
        ticket_summary_section()
    else:
        analytics_dashboard_section()


if __name__ == "__main__":
    main()
