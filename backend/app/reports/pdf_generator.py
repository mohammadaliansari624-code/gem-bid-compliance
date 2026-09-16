import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_compliance_pdf(tender_title: str, results: list) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1a365d')
    )
    story.append(Paragraph("GeM Bid Compliance Verification Report", title_style))
    story.append(Paragraph(f"<b>Tender:</b> {tender_title}", styles['Normal']))
    story.append(Spacer(1, 16))

    # Table Header & Data
    table_data = [["Category", "Status", "Confidence", "Evidence & Reason"]]
    
    for r in results:
        status_text = r.get("status", "")
        conf_text = f"{int(r.get('confidence', 0) * 100)}%"
        cat_text = r.get("category", "")
        evidence_reason = f"<b>Evidence:</b> {r.get('evidence') or 'N/A'}<br/><b>Reason:</b> {r.get('reason') or ''}"
        
        table_data.append([
            Paragraph(cat_text, styles['Normal']),
            Paragraph(status_text, styles['Normal']),
            Paragraph(conf_text, styles['Normal']),
            Paragraph(evidence_reason, styles['Normal'])
        ])

    t = Table(table_data, colWidths=[110, 90, 70, 270])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer