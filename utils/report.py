"""
One-page PDF summary — a leave-behind artifact for recruiters/reviewers who
won't run the app themselves. Built with reportlab (Platypus) so it needs no
external system dependencies.
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

NAVY = colors.HexColor("#0F3057")
TEAL = colors.HexColor("#2E86AB")
LIGHT = colors.HexColor("#F4F7FA")


def build_summary_pdf(kpis: dict, insights: list[tuple[str, str]]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleBig", parent=styles["Title"], textColor=NAVY, fontSize=20, spaceAfter=2)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=colors.grey, fontSize=10, spaceAfter=14)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=NAVY, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13.5)

    story = [
        Paragraph("🏏 Cricbuzz LiveStats — Executive Summary", title_style),
        Paragraph("Real-time cricket analytics platform · SQL warehouse · 25 analytics questions · P Suman Sangeet", subtitle_style),
    ]

    # KPI table
    kpi_items = list(kpis.items())
    kpi_row_labels = [k for k, _ in kpi_items]
    kpi_row_values = [str(v) for _, v in kpi_items]
    kpi_table = Table([kpi_row_labels, kpi_row_values], hAlign="LEFT")
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
    ]))
    story.append(kpi_table)

    story.append(Paragraph("Headline Insights", h2))
    for title, text in insights:
        story.append(Paragraph(f"<b>{title}.</b> {text}", body))
        story.append(Spacer(1, 5))

    story.append(Paragraph("Tech Stack", h2))
    story.append(Paragraph(
        "Python · SQLite (3NF, 7 FK indexes) · 25 tiered SQL analytics questions "
        "(window functions, CTEs, ranking) · Streamlit multi-page app · Plotly interactive "
        "visuals · transaction-safe CRUD · optional live Cricbuzz REST API integration.",
        body,
    ))

    doc.build(story)
    return buf.getvalue()
