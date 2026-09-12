from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from accounts.emails import send_school_verification_decision
from accounts.models import Address, Profile, SchoolVerification


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_type', 'location')
    list_filter = ('account_type', 'location')
    search_fields = ('user__username', 'user__email')


@admin.register(SchoolVerification)
class SchoolVerificationAdmin(admin.ModelAdmin):
    list_display = ("school_name", "staff_name", "owner_name", "status", "submitted_at")
    list_filter = ("status", "first_time_buyer")
    search_fields = ("school_name", "staff_name", "owner_name", "owner_phone", "profile__user__email")
    readonly_fields = ("profile", "submitted_at", "reviewed_at", "forms", "photo")
    actions = ("approve_selected", "reject_selected")
    fieldsets = (
        ("Review", {"fields": ("status", "review_notes", "forms", "photo",
                               "profile", "submitted_at", "reviewed_at")}),
        ("School", {"fields": ("school_name", "school_address", "first_time_buyer",
                               "years_as_customer", "number_of_branches")}),
        ("Average books per class", {"fields": (
            ("books_ages_2_3", "books_ages_3_4", "books_ages_4_5"),
            ("books_basic_1", "books_basic_2", "books_basic_3"),
            ("books_basic_4", "books_basic_5", "books_basic_6"))}),
        ("School owner", {"fields": ("owner_name", "owner_phone")}),
        ("Authorized staff", {"fields": ("staff_name", "staff_post")}),
        ("Declarations", {"fields": ("mandate_declaration_name", "mandate_agreed",
                                     "consent_declaration_name", "consent_agreed")}),
    )

    @admin.display(description="Filled forms")
    def forms(self, obj):
        if not obj.pk:
            return "-"
        mandate = reverse("school_verification_pdf", args=[obj.pk, "mandate"])
        consent = reverse("school_verification_pdf", args=[obj.pk, "consent"])
        return format_html(
            '<a class="button" href="{}" target="_blank">Mandate form (PDF)</a>&nbsp;'
            '<a class="button" href="{}" target="_blank">Consent form (PDF)</a>',
            mandate, consent)

    @admin.display(description="Passport photograph")
    def photo(self, obj):
        if not obj.pk or not obj.passport_photo:
            return "-"
        return format_html('<img src="{}" style="max-height:160px;border:1px solid #ccc;">',
                           reverse("school_verification_photo", args=[obj.pk]))

    def _set_status(self, request, queryset, status):
        # Iterated rather than queryset.update() so each school gets the
        # decision email - these are reviewed in small batches.
        count = 0
        for verification in queryset:
            verification.status = status
            verification.reviewed_at = timezone.now()
            verification.save(update_fields=["status", "reviewed_at"])
            send_school_verification_decision(verification)
            count += 1
        self.message_user(
            request, f"{count} school(s) marked {status.lower()} and notified by email.", messages.SUCCESS)

    @admin.action(description="Approve selected schools (allows checkout)")
    def approve_selected(self, request, queryset):
        self._set_status(request, queryset, SchoolVerification.Status.APPROVED)

    @admin.action(description="Reject selected schools (lets them resubmit)")
    def reject_selected(self, request, queryset):
        self._set_status(request, queryset, SchoolVerification.Status.REJECTED)

    def save_model(self, request, obj, form, change):
        decided = change and "status" in form.changed_data and obj.status in (
            SchoolVerification.Status.APPROVED, SchoolVerification.Status.REJECTED)
        if decided:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
        if decided:
            send_school_verification_decision(obj)
            self.message_user(request, f"{obj.school_name} has been notified by email.", messages.INFO)


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Address)
