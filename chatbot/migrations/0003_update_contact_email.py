from django.db import migrations

OLD_CONTENT = "Phone: +234-907-776-5490. Email: info@learnritepublishers.com."
NEW_CONTENT = "Phone: +234-907-776-5490. Email: learninsideout@yahoo.com."


def update_contact_email(apps, schema_editor):
    """The learnritepublishers.com mailbox isn't set up, so the client is
    using a Yahoo address for now - updates the CONTACT section already
    seeded by migration 0002 on existing databases."""
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    KnowledgeSection.objects.filter(section='CONTACT', content=OLD_CONTENT).update(content=NEW_CONTENT)


def revert_contact_email(apps, schema_editor):
    KnowledgeSection = apps.get_model('chatbot', 'KnowledgeSection')
    KnowledgeSection.objects.filter(section='CONTACT', content=NEW_CONTENT).update(content=OLD_CONTENT)


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0002_seed_knowledge_sections'),
    ]

    operations = [
        migrations.RunPython(update_contact_email, revert_contact_email),
    ]
