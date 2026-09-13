import secrets
from decimal import Decimal

from django.contrib import auth
from django.db import models

from store.models import Book, BookPrice


class SalesRep(models.Model):
    """A field staff member who logs physical school sales as invoices.
    Distinct from Profile/BookPrice.AccountType - reps aren't customers and
    have no pricing tier of their own."""
    user = models.OneToOneField(
        auth.get_user_model(), on_delete=models.CASCADE, related_name="sales_rep")
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email

    @property
    def is_approved(self):
        verification = getattr(self, "employment_verification", None)
        return verification is not None and verification.is_approved

    @property
    def passport_photo(self):
        """The rep's display picture across the app - the same passport
        photograph submitted on their employment form."""
        verification = getattr(self, "employment_verification", None)
        return verification.passport_photo if verification else None


class IDType(models.TextChoices):
    """Shared between the applicant and their guarantor - both identify
    themselves the same way on a Nigerian employment/guarantor form pair."""
    NATIONAL_ID = "NATIONAL_ID", "National ID (NIN)"
    VOTERS_CARD = "VOTERS_CARD", "Voter's Card"
    DRIVERS_LICENSE = "DRIVERS_LICENSE", "Driver's License"
    PASSPORT = "PASSPORT", "International Passport"


class EmploymentVerification(models.Model):
    """The employment form (plus indemnity declaration) a new sales rep
    must complete before they can log invoices - reviewed by staff the same
    way school mandate/consent forms are (see accounts.models.
    SchoolVerification). Fields follow the standard Nigerian employment-form
    layout for field sales/agent roles: bio-data, means of identification,
    BVN and bank details (for commission payment and traceability, common
    for roles that handle company stock or cash), next of kin, and a
    guarantor (see Guarantor below)."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"

    class MaritalStatus(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        MARRIED = "MARRIED", "Married"
        DIVORCED = "DIVORCED", "Divorced"
        WIDOWED = "WIDOWED", "Widowed"

    sales_rep = models.OneToOneField(
        SalesRep, on_delete=models.CASCADE, related_name="employment_verification")

    # Bio-data
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(choices=Gender.choices, max_length=10)
    marital_status = models.CharField(choices=MaritalStatus.choices, max_length=20)
    state_of_origin = models.CharField(max_length=100)
    local_government_area = models.CharField(max_length=100, verbose_name="Local Government Area")
    home_address = models.TextField(verbose_name="Residential address")
    phone_number = models.CharField(max_length=20)

    # Means of identification
    id_type = models.CharField(choices=IDType.choices, max_length=20)
    id_number = models.CharField(max_length=50)
    # Also used as this rep's display picture wherever the app shows one
    # (dashboard, admin listing) - stored in the database rather than on
    # disk, since Render's filesystem is ephemeral and an uploaded file
    # would vanish on the next deploy.
    passport_photo = models.BinaryField(editable=False)
    passport_photo_content_type = models.CharField(max_length=50, editable=False)

    # Bank verification number and bank details - standard on a Nigerian
    # sales/agent employment form, both for commission payment and as a
    # traceable identifier since these roles handle company stock or cash.
    bank_verification_number = models.CharField(
        max_length=11, verbose_name="BVN",
        help_text="Your 11-digit Bank Verification Number.")
    bank_name = models.CharField(max_length=100)
    bank_account_number = models.CharField(max_length=10)
    bank_account_name = models.CharField(max_length=150)

    next_of_kin_name = models.CharField(max_length=150)
    next_of_kin_relationship = models.CharField(max_length=100)
    next_of_kin_phone = models.CharField(max_length=20)
    next_of_kin_address = models.TextField()

    declaration_name = models.CharField(
        max_length=150,
        help_text="Typed name standing in for a signature on the indemnity declaration.")
    agreed = models.BooleanField(default=False)

    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PENDING)
    review_notes = models.TextField(blank=True, help_text="Internal - why this was approved or rejected.")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.get_status_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED


class Guarantor(models.Model):
    """The guarantor's form - one guarantor vouches for the applicant and
    undertakes to make good any loss if the rep absconds with company stock
    or funds, standard practice in Nigeria for field sales/agent roles.
    Submitted alongside EmploymentVerification as one review; approving or
    rejecting the employment form covers this too."""

    employment_verification = models.OneToOneField(
        EmploymentVerification, on_delete=models.CASCADE, related_name="guarantor")

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    occupation = models.CharField(max_length=150)
    employer_name = models.CharField(max_length=150, verbose_name="Employer/place of work")
    office_address = models.TextField()
    home_address = models.TextField(verbose_name="Residential address")
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    relationship_to_applicant = models.CharField(max_length=100)
    years_known = models.PositiveIntegerField(verbose_name="Number of years known")

    id_type = models.CharField(choices=IDType.choices, max_length=20)
    id_number = models.CharField(max_length=50)
    passport_photo = models.BinaryField(editable=False)
    passport_photo_content_type = models.CharField(max_length=50, editable=False)

    declaration_name = models.CharField(
        max_length=150,
        help_text="Typed name standing in for a signature on the guarantor's undertaking above.")
    agreed = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


def _generate_invoice_number():
    return "INV-" + secrets.token_hex(4).upper()


def _generate_receipt_number():
    return "RCT-" + secrets.token_hex(4).upper()


class Invoice(models.Model):
    """A physical sale a rep is handling: the school has already confirmed
    the order in person, and the rep logs it here while payment is still
    outstanding. Marking it paid auto-generates the Receipt."""

    class Status(models.TextChoices):
        PENDING_PAYMENT = "PENDING_PAYMENT", "Pending Payment"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    # Nullable/SET_NULL rather than PROTECT: a rep's account can be deleted
    # completely (see SalesRepAdmin.delete_completely) without touching the
    # financial record of what they sold. sales_rep_name snapshots who
    # issued it at creation time, same as InvoiceItem.title snapshots the
    # book's title, so the invoice/receipt still reads correctly once the
    # rep is gone.
    sales_rep = models.ForeignKey(SalesRep, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="invoices")
    sales_rep_name = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=20, unique=True, default=_generate_invoice_number)
    customer_name = models.CharField(max_length=200, help_text="School or institution name.")
    customer_address = models.TextField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    # Institution pricing has a Lagos/outside-Lagos tier like everywhere
    # else on the site - needed to know which BookPrice to show/charge.
    location = models.CharField(
        choices=BookPrice.Location.choices, max_length=20,
        verbose_name="Customer's location", help_text="Determines the institution price for each book.")
    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PENDING_PAYMENT)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.invoice_number} ({self.customer_name})"

    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0"))


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    title = models.CharField(max_length=70)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.title}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Receipt(models.Model):
    """Auto-created the moment a rep confirms payment on an invoice - never
    created any other way, so its existence alone means payment is in."""
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=20, unique=True, default=_generate_receipt_number)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number
