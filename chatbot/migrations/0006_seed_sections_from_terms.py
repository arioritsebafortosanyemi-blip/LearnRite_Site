from django.db import migrations

# Drawn from the published Terms of Use (store/templates/store/terms_of_use.html)
# so the chatbot can never contradict the policy customers can read for
# themselves. Seeded with get_or_create - anything the client has already
# edited in admin is left alone.
SECTIONS = {
    "SHIPPING": (
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
    ),
    "RETURNS": (
        "Cancellations: a customer can request cancellation by email before their payment has been "
        "verified. Once an order has been dispatched it can't be cancelled.\n"
        "Damaged, defective or incorrect items: the customer should contact us within 7 days of "
        "delivery, and we'll arrange a replacement or a refund at our discretion.\n"
        "Both are handled by email rather than automatically on the site, so direct the customer to "
        "contact the office."
    ),
    "GENERAL": (
        "LearnRite International Publishers is a Nigerian educational publishing company, headquartered "
        "in Lagos, that researches, writes, publishes and distributes textbooks and learning resources "
        "for pupils across Nigeria and wider Africa. Subjects include English language, Mathematics, "
        "Verbal Reasoning, Quantitative Reasoning and Phonics, alongside story books.\n"
        "Books are sold directly to verified schools and to individual customers through the office - "
        "they are not stocked in bookshops.\n"
        "Other things customers can do on the site: leave a star rating on a book they've purchased "
        "(ratings are public), and save books to a wishlist. A wishlist doesn't reserve a book's price "
        "or stock - both can change before checkout.\n"
        "You are an automated assistant. Prices and order statuses you give always come from live "
        "records, but for anything critical the customer should confirm with our staff directly."
    ),
}


def seed_sections(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    for section, content in SECTIONS.items():
        KnowledgeSection.objects.get_or_create(section=section, defaults={'content': content})


def remove_sections(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    KnowledgeSection.objects.filter(section__in=SECTIONS.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0005_seed_signup_section'),
    ]

    operations = [
        migrations.RunPython(seed_sections, remove_sections),
    ]
