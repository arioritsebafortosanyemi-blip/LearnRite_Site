import uuid
from io import BytesIO

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from store.models import BookPrice
from accounts.models import Address, Profile, SchoolVerification


class RegisterForm(UserCreationForm):
    """Deliberately minimal - just enough to create the account. Account
    type, location, organization name, phone and address are all collected
    afterward in one place (see AccountSetupForm/AddressSetupForm), whether
    the customer registered here or signed up with Google."""
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

    class Meta:
        model = Profile
        fields = ("account_type", "location", "organization_name", "phone_number")

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


class AddressSetupForm(forms.ModelForm):
    """Collected alongside AccountSetupForm so checkout can auto-fill a
    default delivery address - full_name/phone_number come from the
    account itself rather than being asked a second time."""

    class Meta:
        model = Address
        fields = ("address_line1", "address_line2", "landmark", "city", "state")


MAX_PHOTO_BYTES = 5 * 1024 * 1024
PHOTO_MAX_EDGE = 600


class SchoolVerificationForm(forms.ModelForm):
    """The mandate and consent forms as one submission. Declarations are
    accepted by typing the declaring name and ticking the affirmation,
    mirroring the 'I, ...' line on each paper form."""

    passport_photo = forms.ImageField(
        label="Passport photograph of authorized staff",
        help_text="A clear head-and-shoulders photo. JPEG or PNG, up to 5MB.")
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
        photo = self.cleaned_data["passport_photo"]
        if photo.size > MAX_PHOTO_BYTES:
            raise forms.ValidationError("That photo is larger than 5MB - please upload a smaller one.")
        return photo

    def save(self, commit=True):
        verification = super().save(commit=False)
        # Downscaled and re-encoded rather than stored as uploaded: these live
        # in the database, and a phone camera original would bloat every row.
        from PIL import Image

        image = Image.open(self.cleaned_data["passport_photo"])
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.thumbnail((PHOTO_MAX_EDGE, PHOTO_MAX_EDGE))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        verification.passport_photo = buffer.getvalue()
        verification.passport_photo_content_type = "image/jpeg"
        if commit:
            verification.save()
        return verification
