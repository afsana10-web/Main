"""
Real PDF report generation with ReportLab. No AI APIs; deterministic layout
from the actual stored inspection/declaration/finding/verification data.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)

from app.models.inspection import Inspection
from app.core.config import settings

NAVY = colors.HexColor("#0B2545")
GREEN = colors.HexColor("#1E7B3C")
AMBER = colors.HexColor("#B7791F")
BLUE = colors.HexColor("#1B5E9C")
RED = colors.HexColor("#B00020")

STATUS_COLORS = {
    "PASS": GREEN,
    "COMPLIANT": GREEN,
    "POTENTIAL_NON_COMPLIANCE": AMBER,
    "NEEDS_VERIFICATION": BLUE,
    "NEEDS_OFFICER_VERIFICATION": BLUE,
    "NOT_APPLICABLE": colors.grey,
}


def generate_inspection_report(
    inspection: Inspection,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{inspection.inspection_code}_report.pdf")

    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PTitle", parent=styles["Title"], textColor=NAVY, fontSize=22)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=NAVY)
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story = []
    story.append(Paragraph("PARAKH", title_style))
    story.append(Paragraph("Scan. Analyse. Verify. &mdash; Legal Metrology Compliance Screening Report", normal))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Automated results are preliminary screening results and require authorized officer verification.</b>",
        ParagraphStyle("Disclaimer", parent=normal, textColor=RED, fontSize=10),
    ))
    story.append(Spacer(1, 14))

    # Inspection info
    info_data = [
        ["Inspection ID", inspection.inspection_code, "Date", inspection.inspection_date.strftime("%d %b %Y")],
        ["Officer", inspection.officer.full_name if inspection.officer else "-", "Location", inspection.location],
        ["Product", inspection.product_name, "Brand", inspection.brand],
        ["Category", inspection.category, "Rule Version", inspection.ruleset_version or settings.CURRENT_RULESET_VERSION],
        ["Overall Status", inspection.status.value, "Generated", datetime.utcnow().strftime("%d %b %Y %H:%M UTC")],
    ]
    t = Table(info_data, colWidths=[85, 155, 85, 145])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("TEXTCOLOR", (2, 0), (2, -1), NAVY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    if inspection.notes:
        story.append(Paragraph("Notes", h2))
        story.append(Paragraph(inspection.notes, normal))
        story.append(Spacer(1, 10))

    # Package images
    story.append(Paragraph("Package Images", h2))
    img_row = []
    for img in inspection.images[:4]:
        path = img.original_path
        if os.path.exists(path):
            try:
                img_row.append(RLImage(path, width=110, height=110))
            except Exception:
                pass
    if img_row:
        story.append(Table([img_row]))
    else:
        story.append(Paragraph("No package images available.", normal))
    story.append(Spacer(1, 14))

    # Declarations
    story.append(Paragraph("Extracted Declarations", h2))
    decl_rows = [["Declaration", "Detected Value", "OCR Confidence", "Verification Needed"]]
    for d in inspection.declarations:
        decl_rows.append([
            Paragraph(d.field.value.replace("_", " ").title(), small),
            Paragraph((d.detected_value or "Not detected")[:120], small),
            f"{d.ocr_confidence:.0f}%" if d.ocr_confidence is not None else "-",
            "Yes" if d.needs_verification else "No",
        ])
    dt = Table(decl_rows, colWidths=[130, 190, 70, 80], repeatRows=1)
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
    ]))
    story.append(dt)
    story.append(Spacer(1, 16))

    # Rule-by-rule compliance checks
    story.append(Paragraph("Rule-by-Rule Compliance Checks", h2))
    check_rows = [["Rule ID", "Declaration", "Status", "Confidence", "Reason"]]
    for c in inspection.checks:
        check_rows.append([
            f"R{c.rule_id} (v{c.rule_version})",
            c.declaration_field.replace("_", " ").title(),
            c.status.value.replace("_", " "),
            f"{c.confidence:.0f}%" if c.confidence is not None else "-",
            Paragraph(c.reason, small),
        ])
    ct = Table(check_rows, colWidths=[70, 90, 90, 55, 165], repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for idx, c in enumerate(inspection.checks, start=1):
        color = STATUS_COLORS.get(c.status.value, colors.black)
        style_cmds.append(("TEXTCOLOR", (2, idx), (2, idx), color))
    ct.setStyle(TableStyle(style_cmds))
    story.append(ct)
    story.append(Spacer(1, 16))

    # Findings + evidence + verification
    if inspection.findings:
        story.append(PageBreak())
        story.append(Paragraph("Findings, Evidence & Officer Verification", h2))
        for f in inspection.findings:
            story.append(Paragraph(f"<b>{f.title}</b>", normal))
            story.append(Paragraph(f"Expected: {f.expected or '-'} &nbsp;&nbsp; Detected: {f.detected or '-'}", normal))
            if f.evidence:
                if f.evidence.status.value == "AVAILABLE":
                    story.append(Paragraph(
                        f"Evidence: bounding box (x={f.evidence.bbox_x}, y={f.evidence.bbox_y}, "
                        f"w={f.evidence.bbox_width}, h={f.evidence.bbox_height}) on source image "
                        f"#{f.evidence.source_image_id}. Extracted text: \"{f.evidence.extracted_text or ''}\"",
                        small,
                    ))
                else:
                    story.append(Paragraph("Evidence region unavailable - officer verification required.", small))
            if f.verification:
                v = f.verification
                story.append(Paragraph(
                    f"Officer Decision: <b>{v.decision.value}</b> &nbsp; "
                    f"Corrected Value: {v.corrected_value or '-'} &nbsp; "
                    f"Remarks: {v.remarks or '-'} &nbsp; "
                    f"Date: {v.verification_date.strftime('%d %b %Y %H:%M')}",
                    normal,
                ))
            else:
                story.append(Paragraph("Officer verification: PENDING", ParagraphStyle("pend", parent=normal, textColor=AMBER)))
            story.append(Spacer(1, 10))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This report was generated by PARAKH, an inspection-assistance and preliminary "
        "compliance-screening system. It does not constitute a final legal determination. "
        f"Rule engine version: {inspection.ruleset_version or settings.CURRENT_RULESET_VERSION}. "
        "OCR Engine: Tesseract OCR.",
        small,
    ))

    doc.build(story)
    return file_path
