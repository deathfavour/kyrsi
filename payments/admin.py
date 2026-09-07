from django.contrib import admin

from config.excel_export import export_queryset_to_xlsx

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "application",
        "status",
        "total_amount",
        "currency",
        "paid_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("invoice_number", "fondy_order_id", "application__full_name")
    readonly_fields = (
        "fondy_order_id",
        "invoice_number",
        "course_price",
        "commission_amount",
        "total_amount",
        "paid_at",
        "created_at",
        "candidate_invoice_pdf",
        "training_center_confirmation_pdf",
        "partner_invoice_pdf",
    )
    date_hierarchy = "created_at"
    actions = ["export_to_excel"]

    @admin.action(description="Export selected payments to Excel")
    def export_to_excel(self, request, queryset):
        columns = [
            ("Invoice Number", lambda p: p.invoice_number),
            ("Applicant", lambda p: p.application.full_name),
            ("Course", lambda p: p.application.course.title),
            ("Status", lambda p: p.get_status_display()),
            ("Currency", lambda p: p.currency.upper()),
            ("Course Price", lambda p: p.course_price),
            ("Commission Amount", lambda p: p.commission_amount),
            ("Total Amount", lambda p: p.total_amount),
            ("Fondy Order ID", lambda p: p.fondy_order_id),
            ("Paid At", lambda p: p.paid_at),
            ("Created At", lambda p: p.created_at),
        ]
        return export_queryset_to_xlsx(queryset, columns, "payments.xlsx")
