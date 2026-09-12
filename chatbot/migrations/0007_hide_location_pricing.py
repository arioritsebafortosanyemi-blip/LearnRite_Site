from django.db import migrations

# The client doesn't want customers knowing that price varies by state, so the
# grounding text no longer mentions location at all - and explicitly tells the
# bot not to explain what a price depends on if asked.
OLD_PRICING = (
    "Individual (personal) accounts never get online pricing or checkout, no matter the order size - "
    "direct them to contact us by email. Only institution (school) accounts see real prices, based on "
    "their account type and delivery location (Lagos or Outside Lagos). Orders of NGN 500,000 or more "
    "get an automatic discount - no code needed."
)
NEW_PRICING = (
    "Individual (personal) accounts never get online pricing or checkout, no matter the order size - "
    "direct them to contact us by email. Only institution (school) accounts see real prices. Orders of "
    "NGN 500,000 or more get an automatic discount - no code needed.\n"
    "Quote a book's price as simply that customer's price. Never say or imply that prices depend on "
    "the customer's state, city or delivery location, and never compare one customer's price to "
    "another's. If asked why a price is what it is, or whether others pay a different amount, don't "
    "speculate - refer them to the office by email or phone."
)


def hide_location_pricing(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    KnowledgeSection.objects.filter(section='PRICING', content=OLD_PRICING).update(content=NEW_PRICING)


def restore_location_pricing(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    KnowledgeSection.objects.filter(section='PRICING', content=NEW_PRICING).update(content=OLD_PRICING)


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0006_seed_sections_from_terms'),
    ]

    operations = [
        migrations.RunPython(hide_location_pricing, restore_location_pricing),
    ]
