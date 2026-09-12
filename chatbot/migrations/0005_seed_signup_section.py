from django.db import migrations

SIGNUP_CONTENT = (
    "Signing up is free and takes three short steps. The customer fills in the forms themselves - "
    "never ask for or accept a password in chat.\n"
    "1. Create the account at /accounts/register/ - full name (schools: the institution's name), "
    "email address (institutions should use the organisation's email), and a password. Passwords need "
    "at least 8 characters, must start with a capital letter, and must include a symbol such as ! @ # or $. "
    "There is also a 'Sign up with Google' button on that page, which skips step 2.\n"
    "2. Verify the email address - we send a verification link to the address given, and the account "
    "can't be used until it's clicked. If it hasn't arrived, check the spam folder or use the "
    "'Resend Verification Email' button shown right after registering.\n"
    "3. Complete the profile - account type (Individual or Institution), location (Lagos or Outside Lagos), "
    "the school/organisation name for institution accounts, a phone number, and a delivery address. "
    "That address is saved and fills in automatically at checkout later.\n"
    "After setup, account type, location, organisation name and email are locked - only the phone number "
    "can be changed from the profile page. Any other change has to be requested by email.\n"
    "Logging in uses the email address and password; there is no separate username. A forgotten password "
    "can be reset from the 'Forgot your password?' link on the login page."
)


def seed_signup_section(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    KnowledgeSection.objects.get_or_create(section='SIGNUP', defaults={'content': SIGNUP_CONTENT})


def remove_signup_section(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    KnowledgeSection.objects.filter(section='SIGNUP').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0004_alter_knowledgesection_section'),
    ]

    operations = [
        migrations.RunPython(seed_signup_section, remove_signup_section),
    ]
