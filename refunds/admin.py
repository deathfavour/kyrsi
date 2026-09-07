from django.contrib import admin, messages
from django.utils import timezone

from config.excel_export import export_queryset_to_xlsx
from payments import fondy
from payments.models import Payment

from .models import RefundRequest


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "payment", "status", "requested_at", "resolved_at", "resolved_by")
    list_filter = ("status",)
    search_fields = ("payment__invoice_number", "payment__application__full_name")
    readonly_fields = ("requested_at",)
    date_hierarchy = "requested_at"
    actions = ["approve_and_process_refund", "reject_request", "export_to_excel"]

    @admin.action(description="Approve and process refund via Fondy")
    def approve_and_process_refund(self, request, queryset):
        """Ручной триггер возврата (см. CLAUDE.md "Модуль возврата" — "Возврат
        через Fondy Refund API — ручной тригер сотрудника из admin, не
        автоматический")."""
        processed = 0
        for refund_request in queryset.select_related("payment"):
            if refund_request.status == RefundRequest.Status.COMPLETED:
                continue
            try:
                fondy.refund_payment(refund_request.payment)
            except fondy.FondyError as exc:
                self.message_user(
                    request,
                    f"Refund #{refund_request.pk} failed: {exc}",
                    level=messages.ERROR,
                )
                continue

            refund_request.status = RefundRequest.Status.COMPLETED
            refund_request.resolved_at = timezone.now()
            refund_request.resolved_by = request.user
            refund_request.save(update_fields=["status", "resolved_at", "resolved_by"])

            refund_request.payment.status = Payment.Status.REFUNDED
            refund_request.payment.save(update_fields=["status"])
            processed += 1

        if processed:
            self.message_user(request, f"{processed} refund(s) processed via Fondy.")

    @admin.action(description="Reject selected refund requests")
    def reject_request(self, request, queryset):
        updated = queryset.exclude(status=RefundRequest.Status.REJECTED).update(
            status=RefundRequest.Status.REJECTED,
            resolved_at=timezone.now(),
            resolved_by=request.user,
        )
        self.message_user(request, f"{updated} refund request(s) rejected.")

    @admin.action(description="Export selected refund requests to Excel")
    def export_to_excel(self, request, queryset):
        columns = [
            ("ID", lambda r: r.pk),
            ("Invoice Number", lambda r: r.payment.invoice_number),
            ("Applicant", lambda r: r.payment.application.full_name),
            ("Reason", lambda r: r.reason),
            ("Status", lambda r: r.get_status_display()),
            ("Requested At", lambda r: r.requested_at),
            ("Resolved At", lambda r: r.resolved_at),
            ("Resolved By", lambda r: str(r.resolved_by) if r.resolved_by else ""),
            ("Notes", lambda r: r.notes or ""),
        ]
        return export_queryset_to_xlsx(queryset, columns, "refund_requests.xlsx")
