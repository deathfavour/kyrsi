from django.conf import settings
from django.db import models

from payments.models import Payment


class RefundRequest(models.Model):
    """Заявка кандидата на возврат средств (см. CLAUDE.md "Модуль возврата").

    Создаётся через Support → «Запросить возврат». Сам возврат через Fondy
    Refund API — ручной триггер сотрудника из admin (RefundRequestAdmin),
    не автоматический."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refund_requests")
    reason = models.TextField()

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Refund #{self.pk} — {self.payment.invoice_number}"
