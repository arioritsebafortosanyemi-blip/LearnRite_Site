from django.db import migrations

# Delivery was removed (checkout is pickup-only now), the order status
# pipeline changed to a payment-first sequence, part payments were added,
# and account setup no longer collects a delivery address - the chatbot's
# admin-editable grounding text still described the old site. Matched
# against the exact old content (seeded by earlier migrations, untouched by
# any later one) so anything the client has since edited in admin is left
# alone, same convention as every migration here.

OLD_SHIPPING = (
    "Customers choose delivery or store pickup at checkout.\n"
    "Delivery: we deliver to the address given at checkout, and send updates to the phone number "
    "or email on the order. An optional landmark can be added to help the delivery team find the "
    "address. Specific delivery details and timing are emailed to the customer once the purchase is "
    "complete - don't quote a delivery timeframe yourself, as timeframes vary by order and location.\n"
    "Pickup: customers who choose store pickup are emailed as soon as their order is ready to "
    "collect. They should bring valid ID and their order reference. If asked where or when to "
    "collect, tell them to contact the office on the phone number or email below to confirm the "
    "pickup location and opening hours.\n"
    "An order moves through Order Received, Processing, Out for Delivery, and Delivered - or "
    "Ready for Pickup and Picked Up for a pickup order. Staff update this manually as the order "
    "progresses, and the customer can see it on their order page.\n"
    "If asked about delivery charges, don't quote a figure - refer the customer to the office by "
    "email or phone to confirm."
)
NEW_SHIPPING = (
    "There is no delivery - every order is collected in store. Once a customer's payment is "
    "confirmed, we email them when their order is ready for pickup; they should bring valid ID and "
    "their order reference.\n"
    "An order moves through this sequence: Pending Payment, then Full Payment Received or Part "
    "Payment Received once a payment is confirmed, then Order Received, then Order Ready for "
    "Pick-up, then Picked Up. It can also be Cancelled at any point. Staff update this manually as "
    "the order progresses, and the customer can see it (plus how much they've paid and any balance "
    "still owed) on their order page.\n"
    "If asked about pickup location or opening hours, don't guess - refer the customer to the "
    "office by phone or email to confirm."
)

OLD_PAYMENT = (
    "Institution accounts place an order online, then pay by bank transfer to the account shown on their "
    "order confirmation page and email. We confirm the order once payment is received - there is no "
    "online card payment yet."
)
NEW_PAYMENT = (
    "Institution accounts place an order online, then pay by bank transfer to the account shown on "
    "their order confirmation page and email. A customer can pay in full, or pay part of the total "
    "now and the rest later - their order page shows the amount paid and any balance still owed, "
    "with a button to submit either a full or a part payment. We confirm each payment before it's "
    "reflected on the order - there is no online card payment yet.\n"
    "A customer can download a PDF invoice for any order at any time from their order page."
)

OLD_SIGNUP = (
    "Signing up is free and takes three short steps. The customer fills in the forms themselves - "
    "never ask for or accept a password in chat.\n"
    "1. Create the account at /accounts/register/ - full name (schools: the institution's name), "
    "email address (institutions should use the organisation's email), and a password. Passwords need "
    "at least 8 characters, must start with a capital letter, and must include a symbol such as ! @ # or $. "
    "There is also a 'Sign up with Google' button on that page, which skips step 2.\n"
    "2. Verify the email address - we send a verification link to the address given, and the account "
    "can't be used until it's clicked. If it hasn't arrived, check the spam folder or use the "
    "'Resend Verification Email' button shown right after registering.\n"
    "3. Complete the profile - account type (Individual or Institution), location (Lagos or Outside Lagos), "
    "the school/organisation name for institution accounts, a phone number, and a delivery address. "
    "That address is saved and fills in automatically at checkout later.\n"
    "After setup, account type, location, organisation name and email are locked - only the phone number "
    "can be changed from the profile page. Any other change has to be requested by email.\n"
    "Logging in uses the email address and password; there is no separate username. A forgotten password "
    "can be reset from the 'Forgot your password?' link on the login page."
)
NEW_SIGNUP = (
    "Signing up is free and takes three short steps. The customer fills in the forms themselves - "
    "never ask for or accept a password in chat.\n"
    "1. Create the account at /accounts/register/ - full name (schools: the institution's name), "
    "email address (institutions should use the organisation's email), and a password. Passwords need "
    "at least 8 characters, must start with a capital letter, and must include a symbol such as ! @ # or $. "
    "There is also a 'Sign up with Google' button on that page, which skips step 2.\n"
    "2. Verify the email address - we send a verification link to the address given, and the account "
    "can't be used until it's clicked. If it hasn't arrived, check the spam folder or use the "
    "'Resend Verification Email' button shown right after registering.\n"
    "3. Complete the profile - account type (Individual or Institution), location (Lagos or Outside "
    "Lagos), the school/organisation name for institution accounts, and a phone number. Institution "
    "accounts can also say whether they already work with a LearnRite sales rep - that's optional "
    "and just for our records, not required to sign up.\n"
    "After setup, account type, location, organisation name and email are locked - only the phone number "
    "can be changed from the profile page. Any other change has to be requested by email.\n"
    "Logging in uses the email address and password; there is no separate username. A forgotten password "
    "can be reset from the 'Forgot your password?' link on the login page."
)

OLD_RETURNS = (
    "Cancellations: a customer can request cancellation by email before their payment has been "
    "verified. Once an order has been dispatched it can't be cancelled.\n"
    "Damaged, defective or incorrect items: the customer should contact us within 7 days of "
    "delivery, and we'll arrange a replacement or a refund at our discretion.\n"
    "Both are handled by email rather than automatically on the site, so direct the customer to "
    "contact the office."
)
NEW_RETURNS = (
    "Cancellations: a customer can request cancellation by email before their payment has been "
    "verified. Once an order has been marked ready for pickup, it can't be cancelled.\n"
    "Damaged, defective or incorrect items: the customer should contact us within 7 days of "
    "picking up their order, and we'll arrange a replacement or a refund at our discretion.\n"
    "Both are handled by email rather than automatically on the site, so direct the customer to "
    "contact the office."
)

UPDATES = {
    "SHIPPING": (OLD_SHIPPING, NEW_SHIPPING),
    "PAYMENT": (OLD_PAYMENT, NEW_PAYMENT),
    "SIGNUP": (OLD_SIGNUP, NEW_SIGNUP),
    "RETURNS": (OLD_RETURNS, NEW_RETURNS),
}


def update_forward(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    for section, (old, new) in UPDATES.items():
        KnowledgeSection.objects.filter(section=section, content=old).update(content=new)


def update_backward(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    for section, (old, new) in UPDATES.items():
        KnowledgeSection.objects.filter(section=section, content=new).update(content=old)


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0008_pricing_decline_not_deny'),
    ]

    operations = [
        migrations.RunPython(update_forward, update_backward),
    ]
