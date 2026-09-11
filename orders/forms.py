from django import forms

from accounts.models import Address


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("full_name", "phone_number", "address_line1", "address_line2", "city", "state")
