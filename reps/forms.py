import uuid
from io import BytesIO

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory

from reps.models import EmploymentVerification, Guarantor, Invoice, InvoiceItem

MAX_PHOTO_BYTES = 5 * 1024 * 1024
PHOTO_MAX_EDGE = 600


def _downscale_photo(photo):
    # Downscaled and re-encoded rather than stored as uploaded: these live
    # in the database, and a phone camera original would bloat every row.
    from PIL import Image

    image = Image.open(photo)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    image.thumbnail((PHOTO_MAX_EDGE, PHOTO_MAX_EDGE))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


class IDPhotoFormMixin:
    """Shared by EmploymentVerificationForm and GuarantorForm: a
    passport_photo ImageField that's optional when resubmitting (keeps the
    photo already on file), size-checked, and downscaled into the model's
    passport_photo/passport_photo_content_type fields on save."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.passport_photo:
            self.fields["passport_photo"].required = False
            self.fields["passport_photo"].help_text = (
                "Leave empty to keep the photo already on file, or upload a new one to replace it.")

    def clean_passport_photo(self):
        photo = self.cleaned_data.get("passport_photo")
        if photo and photo.size > MAX_PHOTO_BYTES:
            raise forms.ValidationError("That photo is larger than 5MB - please upload a smaller one.")
        return photo

    def save(self, commit=True):
        instance = super().save(commit=False)
        photo = self.cleaned_data.get("passport_photo")
        if photo:
            instance.passport_photo = _downscale_photo(photo)
            instance.passport_photo_content_type = "image/jpeg"
        if commit:
            instance.save()
        return instance


class RepRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # first_name/last_name are blank=True on the built-in User model -
        # required here since every rep needs a real name on file.
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
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
        user.username = f"rep_{uuid.uuid4().hex[:12]}"
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class EmploymentVerificationForm(IDPhotoFormMixin, forms.ModelForm):
    """The employment form and indemnity declaration. Declaration is
    accepted by typing the declaring name and ticking the affirmation,
    mirroring how SchoolVerification handles its own declarations."""

    passport_photo = forms.ImageField(
        label="Passport photograph",
        help_text="A clear head-and-shoulders photo - also used as your display picture in the app. JPEG or PNG, up to 5MB.")
    agreed = forms.BooleanField(
        label="I affirm the indemnity declaration above.")

    class Meta:
        model = EmploymentVerification
        fields = (
            "first_name", "last_name", "date_of_birth", "gender", "marital_status",
            "state_of_origin", "local_government_area", "home_address", "phone_number",
            "id_type", "id_number",
            "bank_verification_number", "bank_name", "bank_account_number", "bank_account_name",
            "next_of_kin_name", "next_of_kin_relationship", "next_of_kin_phone", "next_of_kin_address",
            "declaration_name", "agreed",
        )
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "home_address": forms.Textarea(attrs={"rows": 3}),
            "next_of_kin_address": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_bank_verification_number(self):
        bvn = self.cleaned_data["bank_verification_number"]
        if not bvn.isdigit() or len(bvn) != 11:
            raise forms.ValidationError("Enter your 11-digit BVN.")
        return bvn


class GuarantorForm(IDPhotoFormMixin, forms.ModelForm):
    """The guarantor's form and undertaking, submitted alongside the
    employment form."""

    passport_photo = forms.ImageField(
        label="Guarantor's passport photograph",
        help_text="A clear head-and-shoulders photo of the guarantor. JPEG or PNG, up to 5MB.")
    agreed = forms.BooleanField(
        label="I affirm the guarantor's undertaking above.")

    class Meta:
        model = Guarantor
        fields = (
            "first_name", "last_name", "occupation", "employer_name", "office_address", "home_address",
            "phone_number", "email", "relationship_to_applicant", "years_known",
            "id_type", "id_number",
            "declaration_name", "agreed",
        )
        widgets = {
            "office_address": forms.Textarea(attrs={"rows": 2}),
            "home_address": forms.Textarea(attrs={"rows": 2}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ("customer_name", "customer_address", "customer_phone", "location", "notes")
        widgets = {
            "customer_address": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ("book", "unit_price", "quantity")

    def save(self, commit=True):
        item = super().save(commit=False)
        if item.book_id:
            item.title = item.book.title
        if commit:
            item.save()
        return item


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)
