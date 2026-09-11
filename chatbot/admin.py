from django.contrib import admin

from chatbot.models import KnowledgeSection


@admin.register(KnowledgeSection)
class KnowledgeSectionAdmin(admin.ModelAdmin):
    list_display = ("section",)
