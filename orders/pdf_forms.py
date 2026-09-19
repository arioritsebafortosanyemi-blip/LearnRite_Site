"""Renders a website Order to a downloadable invoice PDF on demand - nothing
is written to disk, keeping it clear of Render's ephemeral filesystem (see
accounts.pdf_forms and reps.pdf_forms, which do the same elsewhere).
"""
from django.contrib.staticfiles.finders import find as find_static

from fpdf import FPDF
from fpdf.enums import XPos, YPos

BRAND = (254, 93, 38)
DARK = (33, 37, 41)
MUTED = (90, 90, 90)
RULE = (200, 200, 200)

COMPANY = "LEARNRITE INTERNATIONAL PUBLISHERS LTD."
STRAPLINE = "(International Standard Book Publishers)"
HEAD_OFFICE = "HEAD OFFICE: 5, Adegbola Street, Lawanson, Surulere, Lagos."
LOGO_SIZE = 18


class _DocPDF(FPDF):
    def header_block(self, title):
        logo_path = find_static("store/apple-touch-icon.png")
        if logo_path:
            self.image(logo_path, x=(self.w - LOGO_SIZE) / 2, y=self.get_y(), w=LOGO_SIZE)
            self.ln(LOGO_SIZE + 2)

        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*DARK)
        self.cell(0, 7, COMPANY, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BRAND)
        self.cell(0, 5, STRAPLINE, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 4, HEAD_OFFICE, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        self.ln(3)
        self.set_draw_color(*RULE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*DARK)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(3)

    def field(self, label, value, label_w=45):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9.5)
        self.cell(label_w, 6, label)
        self.set_font("Helvetica", "B", 9.5)
        self.multi_cell(0, 6, str(value) if value not in (None, "") else "-",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _new_pdf():
    pdf = _DocPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(18, 15, 18)
    return pdf


def _items_table(pdf, order):
    col_widths = (88, 22, 33, 31)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_fill_color(*BRAND)
    pdf.set_text_color(255, 255, 255)
    for width, label in zip(col_widths, ("Book", "Qty", "Unit Price", "Line Total")):
        pdf.cell(width, 7, label, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(*DARK)
    pdf.set_font("Helvetica", "", 9.5)
    for item in order.items.all():
        pdf.cell(col_widths[0], 7, item.title, border=1)
        pdf.cell(col_widths[1], 7, str(item.quantity), border=1, align="C")
        pdf.cell(col_widths[2], 7, f"NGN {item.unit_price:,.2f}", border=1, align="R")
        pdf.cell(col_widths[3], 7, f"NGN {item.line_total:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(sum(col_widths[:3]), 7, "Subtotal", border=1, align="R")
    pdf.cell(col_widths[3], 7, f"NGN {order.subtotal:,.2f}", border=1, align="R")
    pdf.ln()
    if order.discount_amount:
        pdf.cell(sum(col_widths[:3]), 7, "Bulk discount", border=1, align="R")
        pdf.cell(col_widths[3], 7, f"-NGN {order.discount_amount:,.2f}", border=1, align="R")
        pdf.ln()
    if order.coupon_discount_amount:
        label = "Coupon discount" + (f" ({order.coupon.code})" if order.coupon else "")
        pdf.cell(sum(col_widths[:3]), 7, label, border=1, align="R")
        pdf.cell(col_widths[3], 7, f"-NGN {order.coupon_discount_amount:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(sum(col_widths[:3]), 7, "Total", border=1, align="R")
    pdf.cell(col_widths[3], 7, f"NGN {order.total:,.2f}", border=1, align="R")
    pdf.ln()

    if order.amount_paid:
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(46, 125, 50)
        pdf.cell(sum(col_widths[:3]), 7, "Amount Paid", border=1, align="R")
        pdf.cell(col_widths[3], 7, f"NGN {order.amount_paid:,.2f}", border=1, align="R")
        pdf.ln()
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*DARK)
        pdf.cell(sum(col_widths[:3]), 7, "Balance Due", border=1, align="R")
        pdf.cell(col_widths[3], 7, f"NGN {order.balance_due:,.2f}", border=1, align="R")
        pdf.ln()


def build_order_invoice_pdf(order):
    pdf = _new_pdf()
    pdf.header_block("INVOICE")
    pdf.field("Invoice Number", order.order_reference)
    pdf.field("Date", order.created_at.strftime("%d %B %Y"))
    pdf.field("Customer", order.full_name)
    pdf.field("Email", order.email)
    pdf.field("Phone", order.phone_number)
    pdf.field("Status", order.status_display)
    pdf.ln(3)
    _items_table(pdf, order)
    return bytes(pdf.output())
