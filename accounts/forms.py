import uuid

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from store.models import BookPrice
from accounts.models import Address, Profile


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
