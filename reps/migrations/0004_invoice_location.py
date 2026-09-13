from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reps', '0003_split_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='location',
            field=models.CharField(
                choices=[('LAGOS', 'Lagos'), ('OUTSIDE_LAGOS', 'Outside Lagos')],
                default='LAGOS', max_length=20, verbose_name="Customer's location"),
            preserve_default=False,
        ),
    ]
