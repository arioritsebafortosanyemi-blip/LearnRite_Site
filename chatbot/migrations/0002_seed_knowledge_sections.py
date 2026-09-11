from django.db import migrations

# Deliberately minimal and only states facts already true elsewhere in the
# app (pricing rules, payment method, contact details) - the client should
# expand these via admin rather than the chatbot inventing shipping/returns
# policy that isn't actually documented anywhere yet.
INITIAL_SECTIONS = {
    "PRICING": (
        "Individual (personal) accounts never get online pricing or checkout, no matter the order size - "
        "direct them to contact us by email. Only institution (school) accounts see real prices, based on "
        "their account type and delivery location (Lagos or Outside Lagos). Orders of NGN 500,000 or more "
        "get an automatic discount - no code needed."
    ),
    "PAYMENT": (
        "Institution accounts place an order online, then pay by bank transfer to the account shown on their "
        "order confirmation page and email. We confirm the order once payment is received - there is no "
        "online card payment yet."
    ),
    "CONTACT": (
        "Phone: +234-907-776-5490. Email: learninsideout@yahoo.com."
    ),
}


def seed_sections(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    for section, content in INITIAL_SECTIONS.items():
        KnowledgeSection.objects.get_or_create(section=section, defaults={'content': content})


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_sections, noop),
    ]
