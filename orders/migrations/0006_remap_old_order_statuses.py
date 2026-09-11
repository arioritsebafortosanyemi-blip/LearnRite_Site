from django.db import migrations

# Order.Status gained delivery-pipeline granularity (Received/Processing/
# Out for Delivery/Delivered replacing the old flat Paid/Fulfilled). Any
# order already sitting in one of the old values needs remapping so it
# still displays a real label instead of the raw old string.
STATUS_REMAP = {
    'PAID': 'RECEIVED',
    'FULFILLED': 'DELIVERED',
}


def remap_forward(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for old_status, new_status in STATUS_REMAP.items():
        Order.objects.filter(status=old_status).update(status=new_status)


def remap_backward(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for old_status, new_status in STATUS_REMAP.items():
        Order.objects.filter(status=new_status).update(status=old_status)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_payment_claimed_at_alter_order_status'),
    ]

    operations = [
        migrations.RunPython(remap_forward, remap_backward),
    ]
