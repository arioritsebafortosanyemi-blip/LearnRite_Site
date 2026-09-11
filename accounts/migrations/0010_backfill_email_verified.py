from django.db import migrations


def mark_existing_profiles_verified(apps, schema_editor):
    """Email verification is a new requirement - accounts that already
    existed before it shipped were never asked to verify anything, so
    grandfather them in rather than locking out real customers on their
    next visit."""
    Profile = apps.get_model("accounts", "Profile")
    Profile.objects.update(email_verified=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_profile_email_verified'),
    ]

    operations = [
        migrations.RunPython(mark_existing_profiles_verified, noop),
    ]
