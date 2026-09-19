from django import forms


class CheckoutForm(forms.Form):
    """Pickup-only - the client dropped delivery, so this just captures who's
    collecting the order rather than a shipping address."""
    full_name = forms.CharField(max_length=100, label="Full Name")
    phone_number = forms.CharField(max_length=20, label="Phone Number")
    coupon_code = forms.CharField(required=False, label="Coupon Code")
