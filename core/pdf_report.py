import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.units import mm


REPORTS_DIR = "reports"


def _ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def _eligibility_color(eligibility: str):
    return {
        "High":   colors.HexColor("#1D9E75"),
        "Medium": colors.HexColor("#BA7517"),
        "Low":    colors.HexColor("#E24B4A"),
    }.get(eligibility, colors.HexColor("#888780"))


def _risk_color(risk: str):
    return {
        "Low":    colors.HexColor("#1D9E75"),
        "Medium": colors.HexColor("#BA7517"),
        "High":   colors.HexColor("#E24B4A"),
    }.get(risk, colors.HexColor("#888780"))


def _section_heading(text: str, styles) -> Paragraph:
    return Paragraph(text, ParagraphStyle(
        "h2",
        parent=styles["Heading2"],
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#26215C"),
        spaceAfter=8
    ))


# ── Section 1: Recommendation ─────────────────────────────
def _build_recommendation_section(recommendation: dict, styles, story: list):
    if not recommendation or recommendation.get("error"):
        if recommendation and recommendation.get("error"):
            story.append(_section_heading("Smart Loan Recommendation", styles))
            story.append(Paragraph(
                f"⚠ {recommendation['error']}",
                ParagraphStyle("warn", parent=styles["Normal"],
                               fontSize=10,
                               textColor=colors.HexColor("#E24B4A"),
                               spaceAfter=6)
            ))
            if recommendation.get("tip"):
                story.append(Paragraph(
                    f"Tip: {recommendation['tip']}",
                    ParagraphStyle("tip", parent=styles["Normal"],
                                   fontSize=10,
                                   textColor=colors.HexColor("#BA7517"),
                                   spaceAfter=6)
                ))
        return

    story.append(_section_heading("Smart Loan Recommendation", styles))
    r = recommendation

    rec_data = [
        ["Parameter",              "Value"],
        ["Recommended Amount",     f"Rs. {float(r.get('recommended_amount', 0)):,.0f}"],
        ["Monthly EMI",            f"Rs. {float(r.get('recommended_emi',    0)):,.2f}"],
        ["Interest Rate",          f"{r.get('recommended_rate',   0)}% p.a."],
        ["Tenure",                 f"{r.get('recommended_tenure', 0)} years"],
        ["Max EMI Capacity",       f"Rs. {float(r.get('max_emi_capacity', 0)):,.2f}"],
        ["Total Interest Payable", f"Rs. {float(r.get('total_interest',  0)):,.0f}"],
        ["Total Payment",          f"Rs. {float(r.get('total_payment',   0)):,.0f}"],
        ["Debt Ratio (FOIR)",      f"{r.get('foir', 0)}%"],
    ]

    rec_table = Table(rec_data, colWidths=[90*mm, 70*mm])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#EEEDFE")),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.HexColor("#26215C")),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1EFE8")]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D1C7")),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
    ]))
    story.append(rec_table)

    # Risk badge
    risk_badge = Table([[Paragraph(
        f"<font color='white'><b>Risk Level: "
        f"{r.get('risk_tier', 'N/A')}</b></font>",
        ParagraphStyle("risk", fontSize=10,
                       fontName="Helvetica-Bold",
                       textColor=colors.white)
    )]], colWidths=[50*mm])
    risk_badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _risk_color(r.get("risk_tier", "Medium"))),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
    ]))
    story.append(Spacer(1, 8))
    story.append(risk_badge)
    story.append(Spacer(1, 20))


# ── Section 2: Explanation ────────────────────────────────
def _build_explanation_section(explanation: dict, styles, story: list):
    if not explanation:
        return

    story.append(_section_heading("Eligibility Explanation", styles))

    story.append(Paragraph(
        explanation.get("summary", ""),
        ParagraphStyle("summary", parent=styles["Normal"],
                       fontSize=11, leading=16,
                       fontName="Helvetica-Bold",
                       textColor=colors.HexColor("#2C2C2A"),
                       spaceAfter=10)
    ))

    for section in explanation.get("sections", []):
        story.append(Paragraph(
            section["label"],
            ParagraphStyle("sec_label", parent=styles["Normal"],
                           fontSize=10, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#26215C"),
                           spaceAfter=2)
        ))
        story.append(Paragraph(
            section["detail"],
            ParagraphStyle("sec_detail", parent=styles["Normal"],
                           fontSize=10, leftIndent=12, leading=15,
                           textColor=colors.HexColor("#5F5E5A"),
                           spaceAfter=8)
        ))

    tips = explanation.get("tips", [])
    if tips:
        story.append(Paragraph(
            "How to Improve Your Eligibility",
            ParagraphStyle("tips_h", parent=styles["Normal"],
                           fontSize=10, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#BA7517"),
                           spaceAfter=6)
        ))
        for tip in tips:
            story.append(Paragraph(
                f"• {tip}",
                ParagraphStyle("tip_item", parent=styles["Normal"],
                               fontSize=10, leftIndent=10, leading=15,
                               textColor=colors.HexColor("#5F5E5A"),
                               spaceAfter=4)
            ))

    story.append(Spacer(1, 20))


# ── Section 3: Dashboard Metrics ──────────────────────────
def _build_dashboard_section(dashboard: dict, styles, story: list):
    if not dashboard:
        return

    story.append(_section_heading("Financial Dashboard Metrics", styles))

    fmt = lambda n: f"Rs. {float(n):,.0f}"

    dash_data = [
        ["Metric",                  "Value"],
        ["Monthly Income",          fmt(dashboard.get("income",         0))],
        ["Existing EMIs",           fmt(dashboard.get("existing_emi",   0))],
        ["Safe EMI Limit (40%)",    fmt(dashboard.get("safe_emi_limit", 0))],
        ["Remaining EMI Capacity",  fmt(dashboard.get("remaining",      0))],
        ["Current FOIR",            f"{dashboard.get('foir', 0)}%"],
        ["FOIR After New Loan",     f"{dashboard.get('after_loan_foir', 0)}%"],
        ["Affordability",           dashboard.get("affordability", "—")],
        ["Credit Health",           dashboard.get("credit_health",  "—")],
        ["Suggested Interest Rate", f"{dashboard.get('rate', 0)}% p.a."],
    ]

    dash_table = Table(dash_data, colWidths=[90*mm, 70*mm])
    dash_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#EEEDFE")),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.HexColor("#26215C")),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1EFE8")]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D1C7")),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
    ]))
    story.append(dash_table)
    story.append(Spacer(1, 20))


# ── Section 4: Amortization Schedule ─────────────────────
def _build_amortization_section(amortization: list, styles, story: list):
    if not amortization:
        return

    story.append(_section_heading(
        f"Amortization Schedule (First {len(amortization)} Months)", styles
    ))

    # Header + rows
    amort_data = [["Month", "EMI (Rs.)", "Principal (Rs.)",
                   "Interest (Rs.)", "Balance (Rs.)"]]

    for row in amortization:
        amort_data.append([
            str(row["month"]),
            f"{row['emi']:,.2f}",
            f"{row['principal']:,.2f}",
            f"{row['interest']:,.2f}",
            f"{row['balance']:,.2f}",
        ])

    amort_table = Table(
        amort_data,
        colWidths=[20*mm, 35*mm, 38*mm, 35*mm, 38*mm]
    )
    amort_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#EEEDFE")),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.HexColor("#26215C")),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1EFE8")]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D1C7")),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(amort_table)
    story.append(Spacer(1, 20))


# ── Main Generator ────────────────────────────────────────
def generate_loan_report(
    income,
    credit,
    eligibility:    str,
    schemes:        list,
    chat_summary:   str,
    emi_data:       dict = None,
    recommendation: dict = None,
    explanation:    dict = None,
    dashboard:      dict = None,    # ✅ new
    amortization:   list = None,    # ✅ new
) -> str:
    _ensure_reports_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath  = os.path.join(REPORTS_DIR, f"loan_report_{timestamp}.pdf")

    doc    = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm,   bottomMargin=20*mm
    )
    styles = getSampleStyleSheet()
    story  = []

    # ── Title ──────────────────────────────────────────────
    story.append(Paragraph("Loan Eligibility Report", ParagraphStyle(
        "Title", parent=styles["Heading1"],
        fontSize=22, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#26215C"), spaceAfter=4
    )))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        ParagraphStyle("Sub", parent=styles["Normal"],
                       fontSize=10,
                       textColor=colors.HexColor("#5F5E5A"),
                       spaceAfter=6)
    ))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#D3D1C7"), spaceAfter=16
    ))

    # ── Eligibility Badge ──────────────────────────────────
    badge_table = Table([[Paragraph(
        f"<font color='white'><b>Eligibility: {eligibility}</b></font>",
        ParagraphStyle("badge", fontSize=13,
                       fontName="Helvetica-Bold",
                       textColor=colors.white)
    )]], colWidths=[80*mm])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _eligibility_color(eligibility)),
        ("ROUNDEDCORNERS", [6]),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 16))

    # ── Financial Summary ──────────────────────────────────
    story.append(_section_heading("Financial Summary", styles))
    summary_data = [
        ["Field",          "Value"],
        ["Monthly Income", f"Rs. {float(income):,.0f}"],
        ["Credit Score",   str(credit)],
        ["Eligibility",    eligibility],
    ]
    if emi_data:
        summary_data += [
            ["Loan Amount",   f"Rs. {emi_data['P']:,.0f}"],
            ["Interest Rate", f"{emi_data['r']}%"],
            ["Tenure",        f"{emi_data['n']} years"],
            ["Monthly EMI",   f"Rs. {emi_data['emi']:,.2f}"],
        ]

    summary_table = Table(summary_data, colWidths=[70*mm, 90*mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#EEEDFE")),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.HexColor("#26215C")),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1EFE8")]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D1C7")),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # ── New Sections ───────────────────────────────────────
    _build_recommendation_section(recommendation, styles, story)
    _build_explanation_section(explanation,       styles, story)
    _build_dashboard_section(dashboard,           styles, story)
    _build_amortization_section(amortization,     styles, story)

    # ── Government Schemes ─────────────────────────────────
    if schemes:
        story.append(_section_heading("Eligible Government Schemes", styles))
        for scheme in schemes:
            story.append(Paragraph(
                f"• {scheme}",
                ParagraphStyle("scheme", parent=styles["Normal"],
                               fontSize=10, leftIndent=10,
                               textColor=colors.HexColor("#0F6E56"),
                               spaceAfter=5)
            ))
        story.append(Spacer(1, 16))

    # ── AI Advisory Summary ────────────────────────────────
    if chat_summary:
        story.append(_section_heading("AI Advisory Summary", styles))
        story.append(Paragraph(
            chat_summary.replace("\n", "<br/>"),
            ParagraphStyle("body", parent=styles["Normal"],
                           fontSize=10, leading=16,
                           textColor=colors.HexColor("#2C2C2A"))
        ))
        story.append(Spacer(1, 16))

    # ── Footer ─────────────────────────────────────────────
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#D3D1C7"), spaceBefore=10
    ))
    story.append(Paragraph(
        "This report is generated for informational purposes only. "
        "Please consult a certified financial advisor before making loan decisions.",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontSize=8,
                       textColor=colors.HexColor("#888780"),
                       spaceBefore=6)
    ))

    doc.build(story)
    return filepath

