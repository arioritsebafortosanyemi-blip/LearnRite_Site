from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from store.models import BookPrice
from accounts.models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    account_type = forms.ChoiceField(choices=BookPrice.AccountType.choices)
    location = forms.ChoiceField(choices=BookPrice.Location.choices)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2", "account_type", "location")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "account_type": self.cleaned_data["account_type"],
                    "location": self.cleaned_data["location"],
                    "profile_confirmed": True,
                },
            )
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("account_type", "location", "phone_number")


class AccountSetupForm(forms.ModelForm):
    """Shown once to accounts that never went through RegisterForm (Google
    sign-ups), so pricing has a real account_type/location instead of the
    signal-created defaults."""

    class Meta:
        model = Profile
        fields = ("account_type", "location")

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.profile_confirmed = True
        if commit:
            profile.save()
        return profile
