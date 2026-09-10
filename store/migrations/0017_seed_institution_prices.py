from decimal import Decimal

from django.db import migrations

# Matched against the client's Lagos/Outside-Lagos institution price lists
# (PDFs, Sept 2026) by title against the live catalog. Books that appear in
# a price list but don't exist on the site yet, and site books that don't
# appear in either price list, are deliberately left untouched here.
PRICES = {
    "I Can Series Writing & Colouring 1": (Decimal("2150.00"), Decimal("2250.00")),
    "I Can Series Writing & Colouring 2": (Decimal("2250.00"), Decimal("2350.00")),
    "I Can Series Writing & Colouring 3": (Decimal("2350.00"), Decimal("2450.00")),
    "First Step In English 1": (Decimal("2150.00"), Decimal("2250.00")),
    "First Step In English 2": (Decimal("2250.00"), Decimal("2350.00")),
    "First Step In English 3": (Decimal("2450.00"), Decimal("2550.00")),
    "First Step In Mathematics 1": (Decimal("2900.00"), Decimal("2950.00")),
    "First Step In Mathematics 2": (Decimal("2950.00"), Decimal("3150.00")),
    "First Step In Mathematics 3": (Decimal("3250.00"), Decimal("3350.00")),
    "Phonics Inside Out 1": (Decimal("2450.00"), Decimal("2550.00")),
    "Phonics Inside Out 2": (Decimal("2450.00"), Decimal("2550.00")),

    "Quantitative Reasoning Inside Out 1": (Decimal("3150.00"), Decimal("3450.00")),
    "Quantitative Reasoning Inside Out 2": (Decimal("3250.00"), Decimal("3450.00")),
    "Quantitative Reasoning Inside Out 3": (Decimal("3250.00"), Decimal("3450.00")),
    "Quantitative Reasoning Inside Out 4": (Decimal("3350.00"), Decimal("3450.00")),
    "Quantitative Reasoning Inside Out 5": (Decimal("3350.00"), Decimal("3450.00")),
    "Quantitative Reasoning Inside Out 6": (Decimal("3350.00"), Decimal("3450.00")),
    "Verbal Reasoning Inside Out 1": (Decimal("3150.00"), Decimal("3450.00")),
    "Verbal Reasoning Inside Out 2": (Decimal("3250.00"), Decimal("3450.00")),
    "Verbal Reasoning Inside Out 3": (Decimal("3250.00"), Decimal("3450.00")),
    "Verbal Reasoning Inside Out 4": (Decimal("3350.00"), Decimal("3450.00")),
    "Verbal Reasoning Inside Out 5": (Decimal("3350.00"), Decimal("3450.00")),
    "Verbal Reasoning Inside Out 6": (Decimal("3350.00"), Decimal("3450.00")),
    "English Inside Out 1": (Decimal("4950.00"), Decimal("5000.00")),
    "English Inside Out 2": (Decimal("5150.00"), Decimal("5250.00")),
    "English Inside Out 3": (Decimal("5550.00"), Decimal("5750.00")),
    "English Inside Out 4": (Decimal("4950.00"), Decimal("4975.00")),
    "English Inside Out 5": (Decimal("4950.00"), Decimal("5000.00")),
    "English Inside Out 6": (Decimal("4950.00"), Decimal("5000.00")),
    "Mathematics Inside Out 1": (Decimal("3850.00"), Decimal("3950.00")),
    "Mathematics Inside Out 2": (Decimal("3850.00"), Decimal("3950.00")),
    "Mathematics Inside Out 3": (Decimal("4950.00"), Decimal("5100.00")),
    "Mathematics Inside Out 4": (Decimal("5250.00"), Decimal("5350.00")),
    "Mathematics Inside Out 5": (Decimal("5350.00"), Decimal("5550.00")),
    "Mathematics Inside Out 6": (Decimal("5350.00"), Decimal("5450.00")),

    "Common Entrance Preparatory Pack (English) Inside Out": (Decimal("6000.00"), Decimal("6500.00")),
    "Common Entrance Preparatory Pack (Mathematics) Inside Out": (Decimal("6000.00"), Decimal("6500.00")),

    "The Sugar Boy": (Decimal("500.00"), Decimal("550.00")),
    "My Dad's Car": (Decimal("500.00"), Decimal("550.00")),
    "The Peace Maker": (Decimal("550.00"), Decimal("550.00")),
    "Bob And Dan": (Decimal("400.00"), Decimal("450.00")),
    "The Money Box": (Decimal("550.00"), Decimal("550.00")),
    "The Better Home": (Decimal("500.00"), Decimal("550.00")),
    "The Exchange": (Decimal("650.00"), Decimal("750.00")),
    "Ken's Exam": (Decimal("500.00"), Decimal("550.00")),
    "Gburugudu": (Decimal("750.00"), Decimal("850.00")),
    "Man-Made Dinosaur": (Decimal("800.00"), Decimal("800.00")),
    "Tales In My Head": (Decimal("850.00"), Decimal("850.00")),
}


def set_institution_prices(apps, schema_editor):
    Book = apps.get_model('store', 'Book')
    BookPrice = apps.get_model('store', 'BookPrice')

    for title, (lagos_price, outside_lagos_price) in PRICES.items():
        book = Book.objects.filter(title=title).first()
        if book is None:
            continue
        BookPrice.objects.update_or_create(
            book=book, account_type='SCHOOL', location='LAGOS',
            defaults={'price': lagos_price},
        )
        BookPrice.objects.update_or_create(
            book=book, account_type='SCHOOL', location='OUTSIDE_LAGOS',
            defaults={'price': outside_lagos_price},
        )


def noop(apps, schema_editor):
    # Not reversing to None - if these get manually adjusted in admin
    # afterward, an un-migrate shouldn't wipe that out.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_alter_bookprice_account_type'),
    ]

    operations = [
        migrations.RunPython(set_institution_prices, noop),
    ]
