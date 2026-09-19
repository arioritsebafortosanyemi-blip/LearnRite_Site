from django.contrib import auth
from django.db import models

from store.models import Book, BookPrice


class Profile(models.Model):
    """Extra account info every user gets - which price tier and location
    they buy at, self-declared, no verification."""
    user = models.OneToOneField \
        (auth.get_user_model(), on_delete=models.CASCADE, related_name="profile")
    account_type = models.CharField \
        (choices=BookPrice.AccountType.choices, max_length=20,
         default=BookPrice.AccountType.INDIVIDUAL,
         help_text="Self-declared. No verification is performed.")
    location = models.CharField \
        (choices=BookPrice.Location.choices, max_length=20,
         default=BookPrice.Location.LAGOS,
         # Also selects the customer's BookPrice tier, but that is deliberately
         # never said out loud: help_text is rendered on the account setup form,
         # and the client doesn't want customers knowing price varies by state.
         help_text="Self-declared, for our records.")
    phone_number = models.CharField(max_length=20, blank=True)
    organization_name = models.CharField \
        (max_length=150, blank=True,
         help_text="Required for institution accounts - the school/organization's name.")
    profile_confirmed = models.BooleanField \
        (default=False,
         help_text="Whether the customer has explicitly chosen account_type/location "
                    "(as opposed to still sitting on the signal-created defaults, e.g. "
                    "right after a Google sign-up). Once set, account_type/location/"
                    "organization_name are locked - a customer must email us to change them.")
    has_sales_rep = models.BooleanField \
        (default=False,
         help_text="Institution accounts only - whether this school already works with a "
                    "LearnRite sales rep rather than dealing with us directly.")
    sales_rep_name = models.CharField \
        (max_length=150, blank=True,
         help_text="Informational only, not linked to any sales rep account - the rep's name, if known.")
    email_verified = models.BooleanField \
        (default=False,
         help_text="Set once the customer clicks the link in their verification email. "
                    "Google sign-ups are treated as already verified.")

    def __str__(self):
        return f"{self.user.username} ({self.account_type}/{self.location})"

    @property
    def is_verified(self):
        """Google sign-ups arrive with an email Google already verified -
        never make them click a second confirmation link of ours."""
        return self.email_verified or self.user.socialaccount_set.exists()


class Address(models.Model):
    user = models.ForeignKey \
        (auth.get_user_model(), related_name="addresses", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255, verbose_name="Address")
    address_line2 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=255, blank=True, help_text="Optional - a nearby landmark to help with delivery.")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Nigeria")
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}, {self.city}, {self.state}"


class SchoolVerification(models.Model):
    """The Mandate Form and Consent Form the client requires from a school
    before it can order - captured as real fields rather than a scan upload,
    so staff get structured data and the filled forms are rendered back to
    PDF on demand (see accounts.pdf_forms). Fields the two paper forms ask
    for twice (school name/address, owner name/phone) are collected once."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="school_verification")

    # Mandate Part A - about the school
    school_name = models.CharField(max_length=200)
    school_address = models.TextField()
    first_time_buyer = models.BooleanField(
        help_text="Part A: 'First-time Buyer?' - unticked means a returning customer.")
    years_as_customer = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Part A: 'Long-time Customer? How many years?' - blank for a first-time buyer.")
    number_of_branches = models.PositiveIntegerField(default=1)

    # Mandate Part A - average number of books per class, one per level
    books_ages_2_3 = models.PositiveIntegerField(default=0, verbose_name="Ages 2-3")
    books_ages_3_4 = models.PositiveIntegerField(default=0, verbose_name="Ages 3-4")
    books_ages_4_5 = models.PositiveIntegerField(default=0, verbose_name="Ages 4-5")
    books_basic_1 = models.PositiveIntegerField(default=0, verbose_name="Basic 1")
    books_basic_2 = models.PositiveIntegerField(default=0, verbose_name="Basic 2")
    books_basic_3 = models.PositiveIntegerField(default=0, verbose_name="Basic 3")
    books_basic_4 = models.PositiveIntegerField(default=0, verbose_name="Basic 4")
    books_basic_5 = models.PositiveIntegerField(default=0, verbose_name="Basic 5")
    books_basic_6 = models.PositiveIntegerField(default=0, verbose_name="Basic 6")

    # Mandate Part B - school owner
    owner_name = models.CharField(max_length=150)
    owner_phone = models.CharField(max_length=100, help_text="One or more numbers.")

    # Mandate Part C - authorised staff, the person actually ordering
    staff_name = models.CharField(max_length=150)
    staff_post = models.CharField(max_length=150, verbose_name="Current post held")
    # Stored in the database rather than on disk: Render's filesystem is
    # ephemeral, so an uploaded file would vanish on the next deploy.
    passport_photo = models.BinaryField(editable=False)
    passport_photo_content_type = models.CharField(max_length=50, editable=False)

    # A photograph of the school itself (building/signage), so staff can
    # cross-check it against the declared address on Google Maps/Earth -
    # separate from the authorized staff's passport photo above.
    school_photo = models.BinaryField(editable=False, blank=True, default=b"")
    school_photo_content_type = models.CharField(max_length=50, blank=True, editable=False)

    # Part D + consent form declarations. Typed name stands in for the
    # signature; the school stamp has no online equivalent, so staff verify
    # against the invoice/letterhead the paper process already requires.
    mandate_declaration_name = models.CharField(
        max_length=150, help_text="Part D: the name typed into 'I, ...' on the mandate declaration.")
    mandate_agreed = models.BooleanField(default=False)
    consent_declaration_name = models.CharField(
        max_length=150, help_text="Consent form: the name typed into 'I, ...' authorising the stamp.")
    consent_agreed = models.BooleanField(default=False)

    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PENDING)
    review_notes = models.TextField(blank=True, help_text="Internal - why this was approved or rejected.")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.school_name} ({self.get_status_display()})"

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED


class WishlistItem(models.Model):
    """A saved-for-later book. Open to any logged-in account, unlike cart/
    checkout - individuals can't buy but can still save books to ask about."""
    user = models.ForeignKey \
        (auth.get_user_model(), related_name="wishlist_items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
