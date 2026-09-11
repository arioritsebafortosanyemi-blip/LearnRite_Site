from django import forms

from accounts.models import Address


class CheckoutForm(forms.ModelForm):
    coupon_code = forms.CharField(required=False, label="Coupon Code")

    class Meta:
        model = Address
        fields = ("full_name", "phone_number", "address_line1", "address_line2", "city", "state")
