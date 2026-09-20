from django.db import models


class KnowledgeSection(models.Model):
    """Admin-editable grounding text for the chatbot's system prompt. One
    row per topic - small enough to concatenate whole into every request
    rather than building a retrieval/vector system, and editable by the
    client without a deploy."""
    class Section(models.TextChoices):
        PRICING = "PRICING", "Pricing & Account Types"
        SIGNUP = "SIGNUP", "Signing Up & Accounts"
        SHIPPING = "SHIPPING", "Pickup"
        PAYMENT = "PAYMENT", "Payment Methods"
        RETURNS = "RETURNS", "Returns & Refunds"
        CONTACT = "CONTACT", "Contact Info"
        GENERAL = "GENERAL", "General / About"

    section = models.CharField(choices=Section.choices, max_length=20, unique=True)
    content = models.TextField(help_text="Plain text the chatbot can draw on when answering questions on this topic.")

    def __str__(self):
        return self.get_section_display()
