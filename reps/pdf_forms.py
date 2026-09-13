"""Renders an Invoice/Receipt to a downloadable PDF on demand - nothing is
written to disk, keeping it clear of Render's ephemeral filesystem (see
accounts.pdf_forms, which does the same for the mandate/consent forms).
"""
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BRAND = (254, 93, 38)
DARK = (33, 37, 41)
MUTED = (90, 90, 90)
RULE = (200, 200, 200)

COMPANY = "LEARNRITE INTERNATIONAL PUBLISHERS LTD."
STRAPLINE = "(International Standard Book Publishers)"
HEAD_OFFICE = "HEAD OFFICE: 5, Adegbola Street, Lawanson, Surulere, Lagos."


class _DocPDF(FPDF):
    def header_block(self, title):
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


def _items_table(pdf, invoice):
    col_widths = (88, 22, 33, 31)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_fill_color(*BRAND)
    pdf.set_text_color(255, 255, 255)
    for width, label in zip(col_widths, ("Book", "Qty", "Unit Price", "Line Total")):
        pdf.cell(width, 7, label, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(*DARK)
    pdf.set_font("Helvetica", "", 9.5)
    for item in invoice.items.all():
        pdf.cell(col_widths[0], 7, item.title, border=1)
        pdf.cell(col_widths[1], 7, str(item.quantity), border=1, align="C")
        pdf.cell(col_widths[2], 7, f"NGN {item.unit_price:,.2f}", border=1, align="R")
        pdf.cell(col_widths[3], 7, f"NGN {item.line_total:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(sum(col_widths[:3]), 7, "Total", border=1, align="R")
    pdf.cell(col_widths[3], 7, f"NGN {invoice.total:,.2f}", border=1, align="R")
    pdf.ln()


def build_invoice_pdf(invoice):
    pdf = _new_pdf()
    pdf.header_block("INVOICE")
    pdf.field("Invoice Number", invoice.invoice_number)
    pdf.field("Date", invoice.created_at.strftime("%d %B %Y"))
    pdf.field("Issued By", invoice.sales_rep.user.get_full_name() or invoice.sales_rep.user.email)
    pdf.field("Customer", invoice.customer_name)
    if invoice.customer_address:
        pdf.field("Address", invoice.customer_address)
    if invoice.customer_phone:
        pdf.field("Phone", invoice.customer_phone)
    pdf.field("Status", invoice.get_status_display())
    pdf.ln(3)
    _items_table(pdf, invoice)
    return bytes(pdf.output())


def build_receipt_pdf(invoice):
    pdf = _new_pdf()
    pdf.header_block("RECEIPT")
    receipt = invoice.receipt
    pdf.field("Receipt Number", receipt.receipt_number)
    pdf.field("Date", receipt.issued_at.strftime("%d %B %Y"))
    pdf.field("Invoice Number", invoice.invoice_number)
    pdf.field("Issued By", invoice.sales_rep.user.get_full_name() or invoice.sales_rep.user.email)
    pdf.field("Customer", invoice.customer_name)
    pdf.ln(3)
    _items_table(pdf, invoice)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 6, "Payment received in full.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return bytes(pdf.output())
