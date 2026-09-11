from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from store.models import BookPrice
from accounts.models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Institution accounts: please use your organization's email address.")
    account_type = forms.ChoiceField(choices=BookPrice.AccountType.choices)
    location = forms.ChoiceField(choices=BookPrice.Location.choices)
    organization_name = forms.CharField(
        required=False, label="School/Organization Name",
        help_text="Required for institution accounts. Subject to verification.")

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2", "account_type", "location", "organization_name")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("account_type") == BookPrice.AccountType.SCHOOL and not cleaned_data.get("organization_name"):
            self.add_error("organization_name", "Required for institution accounts.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "account_type": self.cleaned_data["account_type"],
                    "location": self.cleaned_data["location"],
                    "organization_name": self.cleaned_data["organization_name"],
                    "profile_confirmed": True,
                },
            )
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
    """Shown once to accounts that never went through RegisterForm (Google
    sign-ups), so pricing has a real account_type/location instead of the
    signal-created defaults."""
    organization_name = forms.CharField(
        required=False, label="School/Organization Name",
        help_text="Required for institution accounts. Subject to verification.")

    class Meta:
        model = Profile
        fields = ("account_type", "location", "organization_name")

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
