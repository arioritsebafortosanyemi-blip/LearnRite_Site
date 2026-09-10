from django.db import migrations


def create_stub_prices(apps, schema_editor):
    Book = apps.get_model('store', 'Book')
    BookPrice = apps.get_model('store', 'BookPrice')
    account_types = ['INDIVIDUAL', 'SCHOOL']
    locations = ['LAGOS', 'OUTSIDE_LAGOS']

    stubs = [
        BookPrice(book=book, account_type=account_type, location=location)
        for book in Book.objects.all()
        for account_type in account_types
        for location in locations
    ]
    BookPrice.objects.bulk_create(stubs, ignore_conflicts=True)


def remove_stub_prices(apps, schema_editor):
    BookPrice = apps.get_model('store', 'BookPrice')
    BookPrice.objects.filter(price__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_bookprice'),
    ]

    operations = [
        migrations.RunPython(create_stub_prices, remove_stub_prices),
    ]
