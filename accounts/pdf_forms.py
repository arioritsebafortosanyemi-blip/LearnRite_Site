"""Renders a submitted SchoolVerification back into the two paper forms it
came from, so staff review something recognisable rather than a table of
fields. Generated on demand for the admin download - nothing is written to
disk, which also keeps it clear of Render's ephemeral filesystem.
"""
from io import BytesIO

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

# Extracted from the original paper forms' own scanned countersignature -
# see the "SCHOOL'S STAMP" line on the mandate form and the letterhead on
# the consent form, both signed by the same person.
CEO_NAME = "Judeson A. Ogberaha"
CEO_TITLE = "CEO/MD - For: LearnRite International Publishers Ltd"
SIGNATURE_WIDTH = 32

BOOK_LEVELS = [
    ("Ages 2-3", "books_ages_2_3"),
    ("Ages 3-4", "books_ages_3_4"),
    ("Ages 4-5", "books_ages_4_5"),
    ("Basic 1", "books_basic_1"),
    ("Basic 2", "books_basic_2"),
    ("Basic 3", "books_basic_3"),
    ("Basic 4", "books_basic_4"),
    ("Basic 5", "books_basic_5"),
    ("Basic 6", "books_basic_6"),
]


class _FormPDF(FPDF):
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

    def part_heading(self, text):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*BRAND)
        self.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)

    def field(self, label, value, label_w=62):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9.5)
        self.cell(label_w, 6, label)
        self.set_font("Helvetica", "B", 9.5)
        self.multi_cell(0, 6, str(value) if value not in (None, "") else "-",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def paragraph(self, text, size=8.5, height=4.6):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", size)
        self.multi_cell(0, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _new_pdf():
    pdf = _FormPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(18, 15, 18)
    return pdf


def _yes_no(value):
    return "Yes" if value else "No"


def build_mandate_pdf(verification):
    pdf = _new_pdf()
    pdf.header_block("MANDATE FORM")

    pdf.part_heading("Part A - School Details")
    pdf.field("School's Name", verification.school_name)
    pdf.field("School's Address", verification.school_address)
    pdf.field("First-time Buyer?", _yes_no(verification.first_time_buyer))
    pdf.field("Long-time Customer?", _yes_no(not verification.first_time_buyer))
    pdf.field("How many years?", verification.years_as_customer or "-")
    pdf.field("Number of Branches", verification.number_of_branches)
    pdf.ln(1)

    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(0, 6, "Average number of books per class:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / 3
    for index, (label, attr) in enumerate(BOOK_LEVELS):
        if index and index % 3 == 0:
            pdf.ln(6)
            pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(col_w * 0.55, 6, f"   {label}")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(col_w * 0.45, 6, str(getattr(verification, attr)))
    pdf.ln(9)

    pdf.part_heading("Part B - School Owner")
    pdf.field("School Owner's Name", verification.owner_name)
    pdf.field("School Owner's Phone number(s)", verification.owner_phone)
    pdf.ln(2)

    pdf.part_heading("Part C - Authorized Staff")
    photo_top = pdf.get_y()
    pdf.field("Name of Authorized Staff", verification.staff_name)
    pdf.field("Current Post Held", verification.staff_post)
    if verification.passport_photo:
        try:
            pdf.image(BytesIO(bytes(verification.passport_photo)),
                      x=pdf.w - pdf.r_margin - 28, y=photo_top, w=28)
        except Exception:
            pass
    # Caption sits clear of the photo box itself (28mm wide, ~34mm tall from
    # photo_top) rather than running under it.
    pdf.set_y(max(pdf.get_y(), photo_top + 36))
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 4, "Passport-size photograph of authorized staff",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    pdf.set_text_color(*DARK)
    pdf.ln(2)

    pdf.part_heading("Part D - Declaration")
    pdf.paragraph(
        f"I, {verification.mandate_declaration_name}, hereby affirm that every piece of information my staff "
        "and I provided in this form is true and consistent. I also affirm that I will not infringe on the "
        "copyright of LearnRite's authors in any way, shape, form or manner. I hereby promise that my school, "
        "my staff or any person(s) associated with me will not resell LearnRite's books to other schools or "
        "bookshops, make photocopies of any LearnRite's books or add more than 10% to the prices fixed by the "
        "company. I promise to take full responsibility arising from any action by my school or its "
        "representative(s) that is contrary to the foregoing."
    )
    pdf.ln(1)
    pdf.paragraph(
        "Please ensure you sign and stamp the invoice or your school's letterhead containing your school's "
        "order. Your authorized staff MUST come with a copy of the invoice or letterhead signed by you and "
        "dated the very day of purchase."
    )
    _signature_block(pdf, verification)
    return _output(pdf)


def build_consent_pdf(verification):
    pdf = _new_pdf()
    pdf.header_block("CONSENT TO STAMP TEXTBOOKS")

    pdf.paragraph(
        "We write to seek your consent regarding the new security measure on our textbooks. This latest "
        "measure was necessitated by a development in the just concluded sales season.", size=9, height=5)
    pdf.ln(1)
    pdf.paragraph(
        "Recently, we discovered that some of our sales representatives are in the habit of diverting "
        "textbooks (bought in the name of some schools) to other schools and unauthorized places. In order to "
        "halt incidents of this illegal transaction, we have decided to stamp the name of your school on every "
        "copy of your order. It is our fervent hope that this measure, if implemented, will help us serve you "
        "better.", size=9, height=5)
    pdf.ln(1)
    pdf.paragraph(
        "As laudable as this idea is, however, it is impossible to do it without your consent and support. We "
        "promise to use your consent for nothing outside the content of this letter. Your orders will be "
        "customized and delivered to your school. We promise that not even a copy of our textbook (bearing "
        "your school's name) will be sold to other schools, workshop owners or individuals.", size=9, height=5)
    pdf.ln(4)

    pdf.set_draw_color(*RULE)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    pdf.field("Name of School", verification.school_name)
    pdf.field("Detailed Address", verification.school_address)
    pdf.field("School Owner's Name", verification.owner_name)
    pdf.field("School Owner's Phone Number(s)", verification.owner_phone)
    pdf.ln(2)

    pdf.part_heading("School Owner Declaration of Consent to Stamp Textbook")
    pdf.paragraph(
        f"I, {verification.consent_declaration_name}, hereby authorize LearnRite International Publishers Ltd "
        f"to stamp my school's name, {verification.school_name}, on every copy of textbooks purchased from the "
        "company henceforth.", size=9, height=5)
    _signature_block(pdf, verification)
    return _output(pdf)


def _signature_block(pdf, verification):
    pdf.ln(6)

    signature_path = find_static("store/ceo_signature.png")
    if signature_path:
        sig_x = pdf.w - pdf.r_margin - SIGNATURE_WIDTH
        sig_y = pdf.get_y()
        try:
            pdf.image(signature_path, x=sig_x, y=sig_y, w=SIGNATURE_WIDTH)
        except Exception:
            pass
        pdf.set_y(sig_y + 17)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 4.5, CEO_NAME, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 4, CEO_TITLE, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MUTED)
    submitted = verification.submitted_at.strftime("%d %B %Y at %H:%M") if verification.submitted_at else "-"
    pdf.multi_cell(
        0, 4.5,
        f"Submitted online by {verification.staff_name} for {verification.school_name} on {submitted}. "
        "The declarations above were accepted electronically; the typed names stand in place of signatures. "
        "The school stamp is still required on the invoice or letterhead accompanying each order.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)


def _output(pdf):
    return bytes(pdf.output())
