from django.db import models

from payments.models import Payment


class SupportTicket(models.Model):
    """Обращение через кнопку Support (см. CLAUDE.md "Служба поддержки").

    Два типа: свободный вопрос и уведомление о запросе возврата (сам возврат
    оформляется отдельной формой refunds — см. "Запросить возврат" в CLAUDE.md,
    "редирект на форму RefundRequest или создаёт SupportTicket")."""

    class TicketType(models.TextChoices):
        QUESTION = "question", "Question"
        REFUND_REQUEST = "refund_request", "Refund Request"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        CLOSED = "closed", "Closed"

    ticket_type = models.CharField(max_length=16, choices=TicketType.choices)
    applicant_name = models.CharField(max_length=255)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=32, blank=True, null=True)
    related_payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets"
    )
    message = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_ticket_type_display()}] {self.applicant_name}"
