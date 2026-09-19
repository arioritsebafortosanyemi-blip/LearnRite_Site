import uuid
from io import BytesIO

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from store.models import BookPrice
from accounts.models import Profile, SchoolVerification


class RegisterForm(UserCreationForm):
    """Deliberately minimal - just enough to create the account. Account
    type, location, organization name and phone are all collected
    afterward in one place (see AccountSetupForm), whether the customer
    registered here or signed up with Google."""
    full_name = forms.CharField(
        label="Full Name / Institution Name", max_length=150,
        help_text="Schools: enter your institution's name.")
    email = forms.EmailField(required=True, help_text="Institution accounts: please use your organization's email address.")

    class Meta:
        model = get_user_model()
        fields = ("full_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django auto-generates a bulleted list of every validator's help
        # text here - dropped in favour of the single summarised callout the
        # template renders, rather than showing the same rules twice.
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = f"user_{uuid.uuid4().hex[:12]}"
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["full_name"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Account type, location, organization name and email are locked once
    set - self-declared pricing/verification info a customer could
    otherwise switch to dodge institution pricing or reuse a verified
    identity. Changes to those go through the office by email instead."""

    class Meta:
        model = Profile
        fields = ("phone_number",)


class AccountSetupForm(forms.ModelForm):
    """The single "complete your profile" step every new account goes
    through once - whether they registered directly or via Google, which
    never asks for any of this."""
    organization_name = forms.CharField(
        required=False, label="School/Organization Name",
        help_text="Required for institution accounts. Subject to verification.")
    phone_number = forms.CharField(label="Phone Number")
    has_sales_rep = forms.BooleanField(
        required=False, label="We already work with a LearnRite sales rep",
        help_text="Institution accounts only - leave unticked if you're dealing with LearnRite directly.")
    sales_rep_name = forms.CharField(
        required=False, label="Sales rep's name",
        help_text="If known - for our records only.")

    class Meta:
        model = Profile
        fields = ("account_type", "location", "organization_name", "phone_number",
                  "has_sales_rep", "sales_rep_name")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("account_type") == BookPrice.AccountType.SCHOOL and not cleaned_data.get("organization_name"):
            self.add_error("organization_name", "Required for institution accounts.")
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.profile_confirmed = True
        if commit:
            profile.save()
        return profile


MAX_PHOTO_BYTES = 5 * 1024 * 1024
PHOTO_MAX_EDGE = 600
# The school photo is checked against Google Earth imagery rather than
# just displayed as a small thumbnail, so it's kept larger than the
# passport photo above.
SCHOOL_PHOTO_MAX_EDGE = 1200


class SchoolVerificationForm(forms.ModelForm):
    """The mandate and consent forms as one submission. Declarations are
    accepted by typing the declaring name and ticking the affirmation,
    mirroring the 'I, ...' line on each paper form."""

    passport_photo = forms.ImageField(
        label="Passport photograph of authorized staff",
        help_text="A clear head-and-shoulders photo. JPEG or PNG, up to 5MB.")
    school_photo = forms.ImageField(
        label="Photograph of the school",
        help_text="A clear photo of the school building or signage, so we can verify it against your "
                   "declared address on Google Earth. JPEG or PNG, up to 5MB.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Resubmitting after a rejection keeps a photo already on file, so
        # only ask for one again when there isn't one.
        if self.instance.pk and self.instance.passport_photo:
            self.fields["passport_photo"].required = False
            self.fields["passport_photo"].help_text = (
                "Leave empty to keep the photo already on file, or upload a new one to replace it.")
        if self.instance.pk and self.instance.school_photo:
            self.fields["school_photo"].required = False
            self.fields["school_photo"].help_text = (
                "Leave empty to keep the photo already on file, or upload a new one to replace it.")
    mandate_agreed = forms.BooleanField(
        label="I affirm the declaration above on behalf of the school.")
    consent_agreed = forms.BooleanField(
        label="I authorize LearnRite to stamp the school's name on every copy ordered.")

    class Meta:
        model = SchoolVerification
        fields = (
            "school_name", "school_address", "first_time_buyer", "years_as_customer",
            "number_of_branches",
            "books_ages_2_3", "books_ages_3_4", "books_ages_4_5",
            "books_basic_1", "books_basic_2", "books_basic_3",
            "books_basic_4", "books_basic_5", "books_basic_6",
            "owner_name", "owner_phone",
            "staff_name", "staff_post",
            "mandate_declaration_name", "mandate_agreed",
            "consent_declaration_name", "consent_agreed",
        )
        widgets = {"school_address": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("first_time_buyer") and not cleaned_data.get("years_as_customer"):
            self.add_error("years_as_customer", "Tell us how many years you've been buying from us.")
        return cleaned_data

    def clean_passport_photo(self):
        photo = self.cleaned_data.get("passport_photo")
        if photo and photo.size > MAX_PHOTO_BYTES:
            raise forms.ValidationError("That photo is larger than 5MB - please upload a smaller one.")
        return photo

    def clean_school_photo(self):
        photo = self.cleaned_data.get("school_photo")
        if photo and photo.size > MAX_PHOTO_BYTES:
            raise forms.ValidationError("That photo is larger than 5MB - please upload a smaller one.")
        return photo

    @staticmethod
    def _downscaled_jpeg(photo, max_edge):
        # Downscaled and re-encoded rather than stored as uploaded: these
        # live in the database, and a phone camera original would bloat
        # every row.
        from PIL import Image

        image = Image.open(photo)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.thumbnail((max_edge, max_edge))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()

    def save(self, commit=True):
        verification = super().save(commit=False)
        passport_photo = self.cleaned_data.get("passport_photo")
        if passport_photo:
            verification.passport_photo = self._downscaled_jpeg(passport_photo, PHOTO_MAX_EDGE)
            verification.passport_photo_content_type = "image/jpeg"
        school_photo = self.cleaned_data.get("school_photo")
        if school_photo:
            verification.school_photo = self._downscaled_jpeg(school_photo, SCHOOL_PHOTO_MAX_EDGE)
            verification.school_photo_content_type = "image/jpeg"
        if commit:
            verification.save()
        return verification
