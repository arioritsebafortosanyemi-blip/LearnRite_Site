from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from reps.emails import send_employment_verification_decision, send_invoice_to_school
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
    fields = ("invoice_number", "customer_name", "status", "total", "commission_rate",
              "commission_amount", "created_at", "paid_at")
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """View-only for regular staff - nobody can edit an invoice/receipt
    after the fact. Anything that needs to change (payment confirmed,
    cancelled) happens through the rep's own portal, so there's always a
    straight record of who did what rather than a figure quietly changed in
    admin. Deleting an old invoice/receipt is reserved for superusers -
    is_staff alone isn't enough, so a compromised or careless staff account
    can't erase a sales record."""
    list_display = ("invoice_number", "customer_name", "customer_phone", "location", "issued_by", "status",
                    "commission_rate", "commission_amount", "created_at", "paid_at")
    list_filter = ("status", "location", "sales_rep")
    search_fields = ("invoice_number", "customer_name", "customer_phone", "customer_email",
                     "sales_rep_name", "sales_rep__user__email")
    readonly_fields = ("invoice_number", "issued_by", "customer_name", "customer_address", "customer_phone",
                       "customer_email", "location", "status", "notes", "discount_amount", "commission_rate",
                       "commission_amount", "created_at", "paid_at", "pdf_links")
    inlines = (InvoiceItemInline, ReceiptInline)
    actions = ("send_to_school",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.action(description="Send invoice to school by email")
    def send_to_school(self, request, queryset):
        count = 0
        skipped = 0
        for invoice in queryset:
            if not invoice.customer_email:
                skipped += 1
                continue
            send_invoice_to_school(invoice)
            count += 1
        message = f"Invoice sent to {count} school(s)."
        if skipped:
            message += f" Skipped {skipped} with no email on file."
        self.message_user(request, message, messages.SUCCESS if count else messages.WARNING)

    @admin.display(description="Issued By", ordering="sales_rep_name")
    def issued_by(self, obj):
        # sales_rep_name is a snapshot taken when the invoice was created,
        # so this still shows correctly after the rep's account is deleted
        # (see SalesRepAdmin.delete_completely).
        return obj.sales_rep_name or "-"

    @admin.display(description="Documents")
    def pdf_links(self, obj):
        if not obj.pk:
            return "-"
        style = ("display:inline-block;padding:6px 14px;margin-right:8px;border-radius:6px;"
                 "background:#fe5d26;color:#fff;font-weight:600;text-decoration:none;")
        internal_style = style.replace("#fe5d26", "#5a5a5a")
        invoice_url = reverse("reps:invoice_pdf", args=[obj.pk])
        internal_url = reverse("reps:internal_invoice_pdf", args=[obj.pk])
        links = format_html(
            '<a style="{}" href="{}" target="_blank">Invoice for school (PDF)</a>'
            '<a style="{}" href="{}" target="_blank">Internal copy with commission (PDF)</a>',
            style, invoice_url, internal_style, internal_url)
        if hasattr(obj, "receipt"):
            receipt_url = reverse("reps:receipt_pdf", args=[obj.pk])
            links += format_html(
                '<a style="{}" href="{}" target="_blank">Receipt (PDF)</a>', style, receipt_url)
        return links


@admin.register(SalesRep)
class SalesRepAdmin(admin.ModelAdmin):
    """Deactivate for a rep who's left but might come back or whose record
    should stay queryable as staff - revokes login immediately (reuses
    Django's own User.is_active) without touching anything else.

    Delete completely for a rep whose account should stop existing on the
    server outright. Django's default per-object Delete is turned off here
    because its cascade-permission check has no way to know Invoice/Receipt
    should survive; delete_completely below does that safely instead -
    Invoice.sales_rep is SET_NULL, and sales_rep_name (snapshotted when each
    invoice was created) keeps every invoice and receipt readable and on
    record after the account is gone."""
    list_display = ("photo_thumb", "rep_name", "phone", "status", "verification_status",
                    "invoice_count", "created_at")
    list_filter = ("user__is_active", "employment_verification__status")
    search_fields = ("user__first_name", "user__last_name", "user__email",
                     "phone_number", "employment_verification__phone_number")
    readonly_fields = ("user", "created_at", "photo_thumb")
    inlines = (InvoiceInline,)
    actions = ("deactivate_selected", "reactivate_selected", "delete_completely")

    def has_delete_permission(self, request, obj=None):
        return False

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

    @admin.action(description="Delete completely (removes the account - invoices/receipts stay on record)")
    def delete_completely(self, request, queryset):
        count = 0
        for rep in queryset:
            rep.invoices.update(sales_rep_name=rep.user.get_full_name() or rep.user.email)
            rep.user.delete()
            count += 1
        self.message_user(
            request, f"{count} sales rep account(s) deleted from the server. "
                     "Their invoices and receipts remain on record under the name they were issued in.",
            messages.SUCCESS)

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
