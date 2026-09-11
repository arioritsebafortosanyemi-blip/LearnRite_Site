from django.db import migrations

# Client asked for these to stop appearing on the site - none matched
# either Lagos/Outside-Lagos price list (see 0017_seed_institution_prices)
# and have sat unpriced since. Unpublished rather than deleted, so the
# catalog entry (and any future price) can simply be restored later.
TITLES_TO_UNPUBLISH = [
    "Shadows And Reflections",
    "Ade In Lagos",
    "The Naughty Brothers",
    "Pot of Fortune",
]


def unpublish_books(apps, schema_editor):
    Book = apps.get_model('store', 'Book')
    Book.objects.filter(title__in=TITLES_TO_UNPUBLISH).update(is_published=False)


def republish_books(apps, schema_editor):
    Book = apps.get_model('store', 'Book')
    Book.objects.filter(title__in=TITLES_TO_UNPUBLISH).update(is_published=True)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0019_book_is_published'),
    ]

    operations = [
        migrations.RunPython(unpublish_books, republish_books),
    ]
