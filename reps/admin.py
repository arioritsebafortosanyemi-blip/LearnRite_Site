from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from reps.emails import send_employment_verification_decision
from reps.models import EmploymentVerification, Guarantor, Invoice, InvoiceItem, Receipt, SalesRep


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ("book", "title", "unit_price", "quantity")
    can_delete = False


class ReceiptInline(admin.StackedInline):
    model = Receipt
    extra = 0
    readonly_fields = ("receipt_number", "issued_at")
    can_delete = False


class InvoiceInline(admin.TabularInline):
    """Shown on a rep's own admin page so staff can see everything a
    specific rep has logged without leaving their profile."""
    model = Invoice
    extra = 0
    fields = ("invoice_number", "customer_name", "status", "created_at", "paid_at")
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer_name", "sales_rep", "status", "created_at", "paid_at")
    list_filter = ("status", "sales_rep")
    search_fields = ("invoice_number", "customer_name", "sales_rep__user__email")
    readonly_fields = ("invoice_number", "sales_rep", "created_at", "paid_at")
    inlines = (InvoiceItemInline, ReceiptInline)


@admin.register(SalesRep)
class SalesRepAdmin(admin.ModelAdmin):
    list_display = ("photo_thumb", "user", "phone_number", "verification_status", "invoice_count", "created_at")
    search_fields = ("user__username", "user__email", "phone_number")
    readonly_fields = ("user", "created_at", "photo_thumb")
    inlines = (InvoiceInline,)

    @admin.display(description="Photo")
    def photo_thumb(self, obj):
        if not obj.passport_photo:
            return "-"
        return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;'
                           'border-radius:50%;border:1px solid #ccc;">',
                           reverse("reps:employment_verification_photo", args=[obj.employment_verification.pk]))

    @admin.display(description="Employment status")
    def verification_status(self, obj):
        verification = getattr(obj, "employment_verification", None)
        return verification.get_status_display() if verification else "Not submitted"

    @admin.display(description="Invoices issued")
    def invoice_count(self, obj):
        return obj.invoices.count()


class GuarantorInline(admin.StackedInline):
    """Read-only here - the guarantor's form is part of what's being
    reviewed on the employment verification itself, not edited separately."""
    model = Guarantor
    extra = 0
    can_delete = False
    fields = ("first_name", "last_name", "occupation", "employer_name", "office_address", "home_address",
              "phone_number", "email", "relationship_to_applicant", "years_known",
              "id_type", "id_number", "photo", "declaration_name", "agreed")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Passport photograph")
    def photo(self, obj):
        if not obj.pk or not obj.passport_photo:
            return "-"
        return format_html('<img src="{}" style="max-height:160px;border:1px solid #ccc;">',
                           reverse("reps:guarantor_photo", args=[obj.pk]))


@admin.register(EmploymentVerification)
class EmploymentVerificationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "sales_rep", "id_type", "status", "submitted_at")
    list_display_links = ("full_name",)
    list_filter = ("status", "id_type")
    search_fields = ("first_name", "last_name", "id_number", "bank_verification_number", "sales_rep__user__email")
    readonly_fields = ("sales_rep", "submitted_at", "reviewed_at", "photo")
    actions = ("approve_selected", "reject_selected")
    inlines = (GuarantorInline,)
    fieldsets = (
        ("Review", {"fields": ("status", "review_notes", "photo", "sales_rep", "submitted_at", "reviewed_at")}),
        ("Applicant", {"fields": (("first_name", "last_name"), "date_of_birth", "gender", "marital_status",
                                  "state_of_origin", "local_government_area",
                                  "home_address", "phone_number", "id_type", "id_number")}),
        ("Bank Details", {"fields": ("bank_verification_number", "bank_name",
                                     "bank_account_number", "bank_account_name")}),
        ("Next of Kin", {"fields": ("next_of_kin_name", "next_of_kin_relationship",
                                    "next_of_kin_phone", "next_of_kin_address")}),
        ("Declaration", {"fields": ("declaration_name", "agreed")}),
    )

    @admin.display(description="Passport photograph")
    def photo(self, obj):
        if not obj.pk or not obj.passport_photo:
            return "-"
        return format_html('<img src="{}" style="max-height:160px;border:1px solid #ccc;">',
                           reverse("reps:employment_verification_photo", args=[obj.pk]))

    def _set_status(self, request, queryset, status):
        # Iterated rather than queryset.update() so each rep gets the
        # decision email - these are reviewed in small batches.
        count = 0
        for verification in queryset:
            verification.status = status
            verification.reviewed_at = timezone.now()
            verification.save(update_fields=["status", "reviewed_at"])
            send_employment_verification_decision(verification)
            count += 1
        self.message_user(
            request, f"{count} applicant(s) marked {status.lower()} and notified by email.", messages.SUCCESS)

    @admin.action(description="Approve selected sales reps (allows invoicing)")
    def approve_selected(self, request, queryset):
        self._set_status(request, queryset, EmploymentVerification.Status.APPROVED)

    @admin.action(description="Reject selected sales reps (lets them resubmit)")
    def reject_selected(self, request, queryset):
        self._set_status(request, queryset, EmploymentVerification.Status.REJECTED)

    def save_model(self, request, obj, form, change):
        decided = change and "status" in form.changed_data and obj.status in (
            EmploymentVerification.Status.APPROVED, EmploymentVerification.Status.REJECTED)
        if decided:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
        if decided:
            send_employment_verification_decision(obj)
            self.message_user(request, f"{obj.full_name} has been notified by email.", messages.INFO)
