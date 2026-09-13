from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reps', '0002_alter_guarantor_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='employmentverification',
            name='first_name',
            field=models.CharField(default='', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employmentverification',
            name='last_name',
            field=models.CharField(default='', max_length=150),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='employmentverification',
            name='full_name',
        ),
        migrations.AddField(
            model_name='guarantor',
            name='first_name',
            field=models.CharField(default='', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='guarantor',
            name='last_name',
            field=models.CharField(default='', max_length=150),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='guarantor',
            name='full_name',
        ),
    ]
