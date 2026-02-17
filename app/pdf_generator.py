from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import BookingInvoiceRequest

# Colour palette
BRAND_DARK = colors.HexColor("#1a1a2e")
BRAND_PRIMARY = colors.HexColor("#16213e")
BRAND_ACCENT = colors.HexColor("#9f9f9f")
BRAND_HIGHLIGHT = colors.HexColor("#e94560")
TABLE_HEADER_BG = colors.HexColor("#9f9f9f")
TABLE_ALT_ROW = colors.HexColor("#f4f6fb")
LIGHT_GRAY = colors.HexColor("#e0e0e0")
WHITE = colors.white


def _currency(value: float, symbol: str) -> str:
    """Format a number as currency."""
    return f"{symbol}{value:,.2f}"


def _build_styles() -> dict:
    """Return a dictionary of custom paragraph styles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "InvoiceTitle",
            parent=base["Title"],
            fontSize=28,
            textColor=BRAND_DARK,
            spaceAfter=2 * mm,
            leading=32,
        ),
        "subtitle": ParagraphStyle(
            "InvoiceSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=6 * mm,
        ),
        "heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=11,
            textColor=BRAND_ACCENT,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        ),
        "normal": ParagraphStyle(
            "NormalText",
            parent=base["Normal"],
            fontSize=10,
            textColor=BRAND_DARK,
            leading=14,
        ),
        "bold": ParagraphStyle(
            "BoldText",
            parent=base["Normal"],
            fontSize=10,
            textColor=BRAND_DARK,
            leading=14,
            fontName="Helvetica-Bold",
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.gray,
            alignment=1,  # centre
        ),
        "notes": ParagraphStyle(
            "Notes",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.gray,
            leading=13,
            spaceBefore=4 * mm,
        ),
    }


def generate_invoice_pdf(data: BookingInvoiceRequest) -> bytes:
    """Generate a polished invoice PDF and return its bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = _build_styles()
    story: list = []

    sym = "$" if data.currency == "USD" else data.currency + " "

    # Header
    header_data = [
        [
            Paragraph("<b>Guide Booker</b>", styles["title"]),
            Paragraph(
                f"<b>INVOICE</b><br/>{data.invoice_number}",
                ParagraphStyle(
                    "InvNum",
                    parent=styles["bold"],
                    fontSize=14,
                    alignment=2,
                    textColor=BRAND_HIGHLIGHT,
                    leading=20,
                ),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=["60%", "40%"])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.5, BRAND_HIGHLIGHT),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))

    # Customer + Dates
    info_left = (
        f"<b>Bill To:</b><br/>"
        f"{data.customer_name}<br/>"
        f"{data.customer_email}<br/>"
        f"{data.customer_address}"
    )
    info_right = (
        f"<b>Booking Date:</b> {data.booking_date.strftime('%B %d, %Y')}<br/>"
        f"<b>Due Date:</b> {data.due_date.strftime('%B %d, %Y')}<br/>"
        f"<b>Guide Name:</b> {data.guide_name}"
    )
    info_data = [
        [
            Paragraph(info_left, styles["normal"]),
            Paragraph(info_right, styles["normal"]),
        ]
    ]
    info_table = Table(info_data, colWidths=["55%", "45%"])
    info_table.setStyle(
        TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")])
    )
    story.append(info_table)
    story.append(Spacer(1, 8 * mm))

    # Line-items table
    col_widths = ["8%", "47%", "12%", "15%", "18%"]
    tbl_data = [
        [
            Paragraph("<b>#</b>", styles["bold"]),
            Paragraph("<b>Description</b>", styles["bold"]),
            Paragraph("<b>Qty</b>", styles["bold"]),
            Paragraph("<b>Unit Price</b>", styles["bold"]),
            Paragraph("<b>Amount</b>", styles["bold"]),
        ]
    ]
    for idx, item in enumerate(data.items, start=1):
        amount = item.quantity * item.unit_price
        tbl_data.append(
            [
                Paragraph(str(idx), styles["normal"]),
                Paragraph(item.description, styles["normal"]),
                Paragraph(str(item.quantity), styles["normal"]),
                Paragraph(_currency(item.unit_price, sym), styles["normal"]),
                Paragraph(_currency(amount, sym), styles["normal"]),
            ]
        )

    items_table = Table(tbl_data, colWidths=col_widths)
    tbl_style = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    # Alternate row colours
    for i in range(1, len(tbl_data)):
        if i % 2 == 0:
            tbl_style.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW))
    items_table.setStyle(TableStyle(tbl_style))
    story.append(items_table)
    story.append(Spacer(1, 6 * mm))

    # Totals
    subtotal = sum(i.quantity * i.unit_price for i in data.items)
    tax_amount = subtotal * data.tax_rate / 100
    total = subtotal + tax_amount - data.discount

    totals_data = [
        [
            "",
            Paragraph("<b>Subtotal</b>", styles["bold"]),
            Paragraph(_currency(subtotal, sym), styles["normal"]),
        ],
        [
            "",
            Paragraph(f"<b>Tax ({data.tax_rate}%)</b>", styles["bold"]),
            Paragraph(_currency(tax_amount, sym), styles["normal"]),
        ],
        [
            "",
            Paragraph(f"<b>Discount</b>", styles["bold"]),
            Paragraph(
                f"−{_currency(data.discount, sym)}", styles["normal"]
            ),
        ],
        [
            "",
            Paragraph("<b>TOTAL</b>", styles["bold"]),
            Paragraph(
                f"<b>{_currency(total, sym)}</b>",
                ParagraphStyle(
                    "TotalValue",
                    parent=styles["bold"],
                    fontSize=13,
                    textColor=BRAND_HIGHLIGHT,
                ),
            ),
        ],
    ]
    totals_table = Table(totals_data, colWidths=["52%", "28%", "20%"])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("LINEABOVE", (1, -1), (-1, -1), 1.5, BRAND_HIGHLIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(totals_table)

    # Notes
    if data.notes:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(f"<i>Notes: {data.notes}</i>", styles["notes"]))

    # Footer
    story.append(Spacer(1, 12 * mm))
    story.append(
        Paragraph(
            "Guide Booker · Professional Tour Guide Services · guidebooker.com",
            styles["footer"],
        )
    )
    story.append(
        Paragraph(
            "This is a computer-generated invoice. No signature required.",
            styles["footer"],
        )
    )

    doc.build(story)
    return buf.getvalue()
