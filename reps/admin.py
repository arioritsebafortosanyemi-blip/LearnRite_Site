from django.contrib import admin, messages
from django.contrib.auth import get_user_model
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

    def has_add_permission(self, request, obj=None):
        return False


class ReceiptInline(admin.StackedInline):
    model = Receipt
    extra = 0
    readonly_fields = ("receipt_number", "issued_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


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
    """View-only - staff can see exactly what a rep sold and track it here,
    but can't edit or delete an invoice/receipt after the fact. Anything
    that needs to change (payment confirmed, cancelled) happens through the
    rep's own portal, so there's always a straight record of who did what
    rather than a figure quietly changed in admin."""
    list_display = ("invoice_number", "customer_name", "location", "sales_rep", "status", "created_at", "paid_at")
    list_filter = ("status", "location", "sales_rep")
    search_fields = ("invoice_number", "customer_name", "sales_rep__user__email")
    readonly_fields = ("invoice_number", "sales_rep", "customer_name", "customer_address", "customer_phone",
                       "location", "status", "notes", "created_at", "paid_at", "pdf_links")
    inlines = (InvoiceItemInline, ReceiptInline)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Documents")
    def pdf_links(self, obj):
        if not obj.pk:
            return "-"
        style = ("display:inline-block;padding:6px 14px;margin-right:8px;border-radius:6px;"
                 "background:#fe5d26;color:#fff;font-weight:600;text-decoration:none;")
        invoice_url = reverse("reps:invoice_pdf", args=[obj.pk])
        if hasattr(obj, "receipt"):
            receipt_url = reverse("reps:receipt_pdf", args=[obj.pk])
            return format_html(
                '<a style="{}" href="{}" target="_blank">Invoice (PDF)</a>'
                '<a style="{}" href="{}" target="_blank">Receipt (PDF)</a>',
                style, invoice_url, style, receipt_url)
        return format_html('<a style="{}" href="{}" target="_blank">Invoice (PDF)</a>', style, invoice_url)


@admin.register(SalesRep)
class SalesRepAdmin(admin.ModelAdmin):
    """A rep who no longer works with the company is deactivated here
    rather than deleted - Invoice.sales_rep is PROTECT-ed against deletion
    anyway (there's no safe way to delete a rep with invoices on record),
    and the point is to keep their invoice/receipt history intact for
    tracking, not lose it. Deactivating revokes login immediately (reuses
    Django's own User.is_active) and the "Active" filter in the sidebar is
    the "former staff" section the invoices/receipts stay visible under."""
    list_display = ("photo_thumb", "rep_name", "phone", "status", "verification_status",
                    "invoice_count", "created_at")
    list_filter = ("user__is_active", "employment_verification__status")
    search_fields = ("user__first_name", "user__last_name", "user__email",
                     "phone_number", "employment_verification__phone_number")
    readonly_fields = ("user", "created_at", "photo_thumb")
    inlines = (InvoiceInline,)
    actions = ("deactivate_selected", "reactivate_selected")

    @admin.display(description="Photo")
    def photo_thumb(self, obj):
        if not obj.passport_photo:
            return "-"
        return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;'
                           'border-radius:50%;border:1px solid #ccc;">',
                           reverse("reps:employment_verification_photo", args=[obj.employment_verification.pk]))

    @admin.display(description="Sales Rep", ordering="user__first_name")
    def rep_name(self, obj):
        # list_display's "user" column would otherwise render as
        # User.__str__(), which is the random internal username
        # (e.g. "rep_81ba4f9f86af"), not the rep's actual name.
        return obj.user.get_full_name() or obj.user.email

    @admin.display(description="Phone Number")
    def phone(self, obj):
        # SalesRep.phone_number is never actually collected anywhere (only
        # read as an initial value on the employment form) - the real
        # number a rep provided lives on their EmploymentVerification.
        verification = getattr(obj, "employment_verification", None)
        return (verification.phone_number if verification else "") or obj.phone_number or "-"

    @admin.display(description="Status", ordering="user__is_active")
    def status(self, obj):
        return "Active" if obj.user.is_active else "Inactive (no longer staff)"

    @admin.action(description="Deactivate selected sales reps (revokes portal access)")
    def deactivate_selected(self, request, queryset):
        count = get_user_model().objects.filter(sales_rep__in=queryset).update(is_active=False)
        self.message_user(
            request, f"{count} sales rep(s) deactivated - they can no longer log in. "
                     "Their invoices and receipts are unchanged.", messages.SUCCESS)

    @admin.action(description="Reactivate selected sales reps (restores portal access)")
    def reactivate_selected(self, request, queryset):
        count = get_user_model().objects.filter(sales_rep__in=queryset).update(is_active=True)
        self.message_user(request, f"{count} sales rep(s) reactivated.", messages.SUCCESS)

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
