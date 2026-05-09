from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = BASE_DIR / "docs" / "GrowwWise_AI_Product_Guide.pdf"
DATASET_PATH = BASE_DIR / "data" / "support_tickets.csv"

GREEN = colors.HexColor("#00A86B")
GREEN_DARK = colors.HexColor("#027A48")
GREEN_SOFT = colors.HexColor("#ECFDF3")
INK = colors.HexColor("#101828")
MUTED = colors.HexColor("#667085")
BORDER = colors.HexColor("#E4E7EC")
BG = colors.HexColor("#F8FAF9")
RED = colors.HexColor("#D92D20")
ORANGE = colors.HexColor("#DC6803")
BLUE_SOFT = colors.HexColor("#EFF8FF")


class ColorBand(Flowable):
    def __init__(self, height: float, color=GREEN) -> None:
        super().__init__()
        self.height = height
        self.color = color

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self.width = available_width
        return available_width, self.height

    def draw(self) -> None:
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=0)


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=12.5,
            leading=18,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=23,
            textColor=INK,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=18,
            textColor=GREEN_DARK,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.7,
            leading=14.2,
            textColor=INK,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=MUTED,
        ),
        "card_title": ParagraphStyle(
            "CardTitle",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=GREEN_DARK,
            spaceAfter=3,
        ),
        "card_body": ParagraphStyle(
            "CardBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=12,
            textColor=INK,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8.6,
            leading=12,
            textColor=INK,
            backColor=colors.HexColor("#F2F4F7"),
            borderColor=BORDER,
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        ),
    }


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullets(items: Iterable[str], styles: dict[str, ParagraphStyle]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item, styles["body"]), leftIndent=10) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=14,
        bulletFontName="Helvetica",
        bulletFontSize=7,
        bulletColor=GREEN,
    )


def card(title: str, body: str, styles: dict[str, ParagraphStyle], bg=colors.white) -> Table:
    table = Table(
        [[p(title, styles["card_title"])], [p(body, styles["card_body"])]],
        colWidths=[2.35 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("ROUNDEDCORNERS", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def kpi_card(label: str, value: str, helper: str, styles: dict[str, ParagraphStyle]) -> Table:
    label_style = ParagraphStyle(
        "KpiLabel",
        parent=styles["small"],
        fontName="Helvetica-Bold",
        textColor=MUTED,
    )
    value_style = ParagraphStyle(
        "KpiValue",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=INK,
    )
    table = Table(
        [[p(label, label_style)], [p(value, value_style)], [p(helper, styles["small"])]],
        colWidths=[1.72 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def table(data: list[list[str]], widths: list[float], styles: dict[str, ParagraphStyle]) -> Table:
    formatted = [[p(cell, styles["card_body"]) for cell in row] for row in data]
    out = Table(formatted, colWidths=widths, repeatRows=1)
    out.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN_SOFT),
                ("TEXTCOLOR", (0, 0), (-1, 0), GREEN_DARK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return out


def get_dataset_kpis() -> dict[str, str]:
    if not DATASET_PATH.exists():
        return {
            "tickets": "420",
            "avg_resolution": "31.4h",
            "escalation": "41.0%",
            "csat": "3.54/5",
        }

    df = pd.read_csv(DATASET_PATH)
    total = len(df)
    avg_resolution = pd.to_numeric(df["resolution_time_hours"], errors="coerce").mean()
    escalation = df["human_escalation_required"].astype(str).str.lower().isin(["true", "1", "yes"]).mean() * 100
    csat = pd.to_numeric(df["csat_score"], errors="coerce").mean()
    return {
        "tickets": f"{total:,}",
        "avg_resolution": f"{avg_resolution:.1f}h",
        "escalation": f"{escalation:.1f}%",
        "csat": f"{csat:.2f}/5",
    }


def add_footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = letter
    canvas.setStrokeColor(BORDER)
    canvas.line(doc.leftMargin, 0.55 * inch, width - doc.rightMargin, 0.55 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 0.35 * inch, "GrowwWise AI Product & Demo Guide")
    canvas.drawRightString(width - doc.rightMargin, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    styles = make_styles()
    kpis = get_dataset_kpis()

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        rightMargin=0.58 * inch,
        leftMargin=0.58 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.72 * inch,
        title="GrowwWise AI Product Guide",
        author="GrowwWise AI",
    )

    story = []

    story.append(ColorBand(0.14 * inch, GREEN))
    story.append(Spacer(1, 0.22 * inch))
    story.append(p("GrowwWise AI", styles["title"]))
    story.append(
        p(
            "AI-powered support intelligence for retail investors",
            styles["subtitle"],
        )
    )
    story.append(
        p(
            "A polished OpenAI + analytics fintech support demo built for a Groww-style retail investing platform.",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))
    story.append(
        Table(
            [
                [
                    card(
                        "What it is",
                        "A Streamlit product demo that combines an AI support copilot with a stakeholder analytics dashboard.",
                        styles,
                        GREEN_SOFT,
                    ),
                    card(
                        "What it proves",
                        "RAG, OpenAI API usage, embeddings, structured JSON, guardrails, Pandas analytics, and product polish.",
                        styles,
                        BLUE_SOFT,
                    ),
                    card(
                        "Who it helps",
                        "Retail investors get clearer support answers; support and product teams get issue intelligence.",
                        styles,
                        colors.white,
                    ),
                ]
            ],
            colWidths=[2.42 * inch, 2.42 * inch, 2.42 * inch],
            hAlign="CENTER",
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Table(
            [
                [
                    kpi_card("Support tickets", kpis["tickets"], "Synthetic dataset", styles),
                    kpi_card("Avg resolution", kpis["avg_resolution"], "Operational metric", styles),
                    kpi_card("Escalation rate", kpis["escalation"], "Human handoff share", styles),
                    kpi_card("Avg CSAT", kpis["csat"], "Customer satisfaction", styles),
                ]
            ],
            colWidths=[1.78 * inch, 1.78 * inch, 1.78 * inch, 1.78 * inch],
            hAlign="CENTER",
        )
    )
    story.append(Spacer(1, 0.18 * inch))
    story.append(p(f"Prepared: {date.today().strftime('%B %d, %Y')}", styles["small"]))
    story.append(PageBreak())

    story.append(p("1. Product Overview", styles["h1"]))
    story.append(
        p(
            "GrowwWise AI is a support intelligence platform concept for a retail investing app. It answers user support questions, classifies issues, summarizes tickets, explains portfolio risk, and analyzes support trends from a realistic mock dataset.",
            styles["body"],
        )
    )
    story.append(
        bullets(
            [
                "For customers: clear, grounded explanations for support and investing education questions.",
                "For support agents: fast classification, urgency detection, and ticket summaries.",
                "For product and operations teams: dashboards that reveal ticket drivers, escalation hotspots, resolution bottlenecks, and CSAT patterns.",
                "For safety: guardrails prevent direct buy/sell recommendations, guaranteed-return claims, and risky financial advice.",
            ],
            styles,
        )
    )

    story.append(p("Core Modules", styles["h2"]))
    story.append(
        table(
            [
                ["Module", "Purpose", "What to show in a demo"],
                ["Ask Assistant", "RAG assistant over mock help docs.", "Ask an SIP/payment/KYC question and show retrieved references."],
                ["Issue Classification", "Structured JSON support triage.", "Show category, urgency, reason, and human escalation badge."],
                ["Portfolio Risk Explainer", "Pandas portfolio analysis plus AI explanation.", "Show allocation charts and educational disclaimer."],
                ["Support Ticket Summary", "Agent-ready summary of a raw complaint.", "Show priority, sentiment, suggested action, and JSON expander."],
                ["Analytics Dashboard", "Dataset-driven support intelligence.", "Show KPIs, charts, filters, AI insights, and data Q&A."],
            ],
            [1.35 * inch, 2.6 * inch, 3.15 * inch],
            styles,
        )
    )

    story.append(p("2. Architecture", styles["h1"]))
    story.append(
        p(
            "The app is intentionally modular so it is easy to explain in an interview. The frontend lives in app.py, reusable styling lives in src/ui.py, and AI/data logic is split into focused modules.",
            styles["body"],
        )
    )
    story.append(
        table(
            [
                ["File", "Role"],
                ["app.py", "Streamlit navigation, page layouts, buttons, spinners, and result rendering."],
                ["src/ui.py", "Custom CSS, branded headers, KPI cards, result cards, badges, and message components."],
                ["src/openai_client.py", "OpenAI client wrapper for Responses API, embeddings, structured JSON, and fallback mode."],
                ["src/rag.py", "Loads help docs, creates embeddings, indexes ChromaDB, retrieves context, and generates grounded answers."],
                ["src/classifier.py", "Classifies support issues into category, urgency, escalation, reason, and next step."],
                ["src/ticket_summary.py", "Creates structured ticket summaries for support agents."],
                ["src/portfolio_analyzer.py", "Reads sample portfolio CSV, computes allocation metrics, and explains risk."],
                ["src/analytics.py", "Loads support ticket dataset, filters data, calculates KPIs, and powers AI insights/Q&A."],
                ["scripts/generate_dataset.py", "Generates a realistic mock support dataset with 420 rows."],
            ],
            [2.0 * inch, 5.1 * inch],
            styles,
        )
    )

    story.append(p("AI Usage", styles["h2"]))
    story.append(
        bullets(
            [
                "OpenAI Responses API generates grounded assistant answers, portfolio explanations, business insights, and dataset Q&A.",
                "OpenAI embeddings power semantic retrieval over the help documentation.",
                "Structured JSON outputs are used for issue classification and ticket summarization.",
                "Fallback responses keep the demo usable when no API key is configured.",
            ],
            styles,
        )
    )

    story.append(PageBreak())
    story.append(p("3. How to Run Locally", styles["h1"]))
    story.append(p("From the project root:", styles["body"]))
    story.append(p("python -m venv .venv<br/>source .venv/bin/activate<br/>pip install -r requirements.txt", styles["code"]))
    story.append(p("Create a local environment file:", styles["body"]))
    story.append(p("cp .env.example .env<br/># Edit .env and add:<br/>OPENAI_API_KEY=your_new_openai_api_key_here", styles["code"]))
    story.append(p("Generate the dataset and start the app:", styles["body"]))
    story.append(p("python scripts/generate_dataset.py<br/>streamlit run app.py", styles["code"]))
    story.append(
        p(
            "Open the local URL shown by Streamlit, usually http://localhost:8501. If no API key is available, the app still runs in demo fallback mode.",
            styles["body"],
        )
    )

    story.append(p("4. How to Use Each Page", styles["h1"]))
    story.append(p("Ask Assistant", styles["h2"]))
    story.append(
        bullets(
            [
                "Open Ask Assistant from the sidebar.",
                "Try: My SIP failed but money got debited. What should I do?",
                "Click Ask GrowwWise AI.",
                "Explain that the app first searches the help knowledge base, then generates a grounded answer.",
                "Open the Retrieved support references expander to show RAG context.",
            ],
            styles,
        )
    )

    story.append(p("Issue Classification", styles["h2"]))
    story.append(
        bullets(
            [
                "Paste a raw support message such as: My KYC keeps getting rejected even after uploading documents.",
                "Click Classify Issue.",
                "Show the cards for category, urgency, human escalation, reason, and suggested next step.",
                "Open Structured JSON only if you want to show model output format.",
            ],
            styles,
        )
    )

    story.append(p("Portfolio Risk Explainer", styles["h2"]))
    story.append(
        bullets(
            [
                "Review the sample portfolio table and KPI cards.",
                "Show risk distribution and asset distribution charts.",
                "Click Generate Portfolio Risk Explanation.",
                "Point out that it explains concentration risk, high-risk exposure, diversification, and includes a financial advice disclaimer.",
            ],
            styles,
        )
    )

    story.append(PageBreak())
    story.append(p("Support Ticket Summary", styles["h2"]))
    story.append(
        bullets(
            [
                "Paste a complaint such as: My SIP failed twice and money got debited both times. I am very frustrated.",
                "Click Summarize Ticket.",
                "Show summary, issue type, priority, sentiment, suggested action, and escalation requirement.",
                "Explain how this can reduce manual support triage time.",
            ],
            styles,
        )
    )

    story.append(p("Analytics Dashboard", styles["h2"]))
    story.append(
        bullets(
            [
                "Open Analytics Dashboard from the sidebar.",
                "Use filters for date range, issue category, priority, status, channel, and customer segment.",
                "Review KPI cards: total tickets, average resolution time, escalation rate, average CSAT, high-priority tickets, and open tickets.",
                "Use charts to explain trends by category, priority, sentiment, resolution time, CSAT, escalation rate, and channel.",
                "Click Generate AI Business Insights to generate stakeholder recommendations from aggregated metrics.",
                "Use Ask Questions About the Dataset for natural language data Q&A.",
            ],
            styles,
        )
    )

    story.append(p("5. Demo Script for an Interview", styles["h1"]))
    story.append(
        table(
            [
                ["Time", "Action", "What to say"],
                ["0:00-0:45", "Open the app and introduce the sidebar.", "GrowwWise AI combines customer-facing AI support with internal support analytics."],
                ["0:45-1:45", "Ask an SIP/payment question.", "This demonstrates RAG: retrieved docs ground the answer and escalation guidance."],
                ["1:45-2:30", "Show Issue Classification.", "The model returns structured support triage data, not just prose."],
                ["2:30-3:15", "Show Ticket Summary.", "This turns raw complaints into agent-ready summaries."],
                ["3:15-4:30", "Show Analytics Dashboard.", "This reveals business metrics such as ticket drivers, escalation rate, CSAT, and resolution bottlenecks."],
                ["4:30-5:00", "Generate AI Insights.", "OpenAI uses aggregated metrics to recommend what support teams should prioritize."],
            ],
            [0.9 * inch, 2.1 * inch, 4.1 * inch],
            styles,
        )
    )

    story.append(p("Strong Interview Pitch", styles["h2"]))
    story.append(
        p(
            "I extended GrowwWise beyond a chatbot into an AI + analytics support intelligence platform. It not only answers user queries using RAG and OpenAI, but also analyzes support ticket data to identify issue trends, escalation drivers, resolution bottlenecks, and customer satisfaction patterns. This makes the project closer to a real fintech use case where AI can support both customers and internal business teams.",
            styles["body"],
        )
    )
    story.append(
        p(
            "I also focused on product polish and user experience. GrowwWise AI includes branded pages, clean dashboard cards, loading states for AI actions, structured result formatting, and stakeholder-ready analytics visualizations.",
            styles["body"],
        )
    )

    story.append(PageBreak())
    story.append(p("6. Deployment Guide", styles["h1"]))
    story.append(
        bullets(
            [
                "GitHub repo: https://github.com/Photon7777/GrowwWise-AI",
                "Streamlit Cloud repository: Photon7777/GrowwWise-AI",
                "Branch: main",
                "Main file path: app.py",
                "Secrets: configure OPENAI_API_KEY in Streamlit Cloud Advanced settings.",
            ],
            styles,
        )
    )
    story.append(p('Streamlit Cloud secret format:', styles["body"]))
    story.append(p('OPENAI_API_KEY = "your_new_openai_api_key_here"', styles["code"]))
    story.append(
        p(
            "Never commit .env or real API keys to GitHub. The app reads OPENAI_API_KEY from Streamlit Cloud secrets in production and from .env locally.",
            styles["body"],
        )
    )

    story.append(p("7. Safety, Privacy, and Guardrails", styles["h1"]))
    story.append(
        bullets(
            [
                "The assistant refuses direct buy/sell recommendations and guaranteed-return claims.",
                "Investment-related explanations include: This is for educational purposes and not financial advice.",
                "Payment failures, KYC issues, account access problems, order execution issues, and compliance-sensitive cases recommend human escalation.",
                "Analytics AI receives aggregated summary statistics, not all raw ticket rows.",
                "The dataset is synthetic and created for demo purposes.",
            ],
            styles,
        )
    )

    story.append(p("8. Troubleshooting", styles["h1"]))
    story.append(
        table(
            [
                ["Issue", "Likely cause", "Fix"],
                ["OpenAI key missing", "No .env locally or no Streamlit secret.", "Add OPENAI_API_KEY to .env locally or Streamlit Cloud secrets."],
                ["Protobuf descriptor error", "Cloud dependency mismatch.", "requirements.txt pins protobuf==3.20.3; clear Streamlit cache and reboot."],
                ["SQLite/Chroma error", "Older cloud SQLite runtime.", "requirements.txt includes pysqlite3-binary for Linux builds."],
                ["Dashboard has no data", "support_tickets.csv missing.", "Run python scripts/generate_dataset.py."],
                ["Old UI still visible", "Browser or Streamlit cache.", "Hard refresh the browser or reboot the Streamlit app."],
            ],
            [1.8 * inch, 2.25 * inch, 3.05 * inch],
            styles,
        )
    )

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        p(
            "End note: GrowwWise AI is a demo application. It does not provide financial advice, legal advice, buy/sell recommendations, or guaranteed-return claims.",
            styles["small"],
        )
    )

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


if __name__ == "__main__":
    build_pdf()
    print(f"Created {OUTPUT_PATH}")
