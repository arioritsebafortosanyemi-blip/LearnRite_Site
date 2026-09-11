from django import forms

from accounts.models import Address
from orders.models import Order

ADDRESS_FIELDS = ("address_line1", "city", "state")


class CheckoutForm(forms.ModelForm):
    coupon_code = forms.CharField(required=False, label="Coupon Code")
    delivery_method = forms.ChoiceField \
        (choices=Order.DeliveryMethod.choices, initial=Order.DeliveryMethod.DELIVERY,
         widget=forms.RadioSelect, label="How would you like to receive your order?")

    class Meta:
        model = Address
        fields = ("full_name", "phone_number", "address_line1", "address_line2", "landmark", "city", "state")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only required for delivery - store pickup needs just a name/phone
        # to identify who's collecting, not a shipping address.
        for field in ADDRESS_FIELDS:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("delivery_method") == Order.DeliveryMethod.DELIVERY:
            for field in ADDRESS_FIELDS:
                if not cleaned_data.get(field):
                    self.add_error(field, "Required for delivery.")
        return cleaned_data
