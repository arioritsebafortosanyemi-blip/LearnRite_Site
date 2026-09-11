from django.db import migrations


def seed_data(apps, schema_editor):
    PaymentAccount = apps.get_model('orders', 'PaymentAccount')
    PaymentAccount.objects.get_or_create(
        account_number='0042380422',
        defaults={
            'bank_name': 'Access Bank',
            'account_name': 'Learnrite International Publishers Limited',
            'active': True,
        },
    )

    BulkDiscountRule = apps.get_model('orders', 'BulkDiscountRule')
    if not BulkDiscountRule.objects.exists():
        BulkDiscountRule.objects.create(
            minimum_order_amount=500000,
            discount_percentage=5,
            active=True,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_bulkdiscountrule_order_paymentaccount_orderitem'),
    ]

    operations = [
        migrations.RunPython(seed_data, noop),
    ]
