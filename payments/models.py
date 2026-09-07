import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from applications.models import Application


def _generate_order_id(application):
    return f"KYRSI-{application.pk}-{uuid.uuid4().hex[:10].upper()}"


def _generate_invoice_number(application):
    return f"INV-{timezone.now():%Y%m%d}-{application.pk:06d}"


class PaymentManager(models.Manager):
    def get_or_init_for_application(self, application):
        """Один Payment на Application (one-to-one). Снэпшот цены/комиссии
        берётся с курса в момент первого обращения к оплате и больше не
        пересчитывается, даже если цены на Course изменятся позже.

        total_amount = Course.price_usd — это то, что видит и платит
        кандидат (заказчик называет её "GMG Academy" — см. CLAUDE.md
        "Прайсинг"), без наценки сверху. course_price — снэпшот доли
        учебного центра (training_center_price_usd, "MMTC"), commission_amount
        — остаток партнёру (price_usd − training_center_price_usd)."""
        try:
            return self.get(application=application), False
        except self.model.DoesNotExist:
            pass

        course = application.course
        total_amount = course.price_usd
        course_price = course.training_center_price_usd
        commission_amount = (total_amount - course_price).quantize(Decimal("0.01"))

        payment = self.create(
            application=application,
            currency=self.model.Currency.USD,
            course_price=course_price,
            commission_amount=commission_amount,
            total_amount=total_amount,
            fondy_order_id=_generate_order_id(application),
            invoice_number=_generate_invoice_number(application),
            status=self.model.Status.PENDING,
        )
        return payment, True


class Payment(models.Model):
    class Currency(models.TextChoices):
        USD = "usd", "USD"
        EUR = "eur", "EUR"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    application = models.OneToOneField(
        Application, on_delete=models.PROTECT, related_name="payment"
    )

    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)
    course_price = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    fondy_order_id = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    invoice_number = models.CharField(max_length=32, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # PDF-документы, привязанные к платежу. Хранятся бессрочно, не удаляются
    # (ISO 9001 / MLC-аудит — см. CLAUDE.md "Безопасность и соответствие стандартам").
    candidate_invoice_pdf = models.FileField(
        upload_to="payments/candidate_invoices/", blank=True
    )
    training_center_confirmation_pdf = models.FileField(
        upload_to="payments/training_center_confirmations/", blank=True
    )
    partner_invoice_pdf = models.FileField(upload_to="payments/partner_invoices/", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = PaymentManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invoice_number} — {self.application.full_name}"

    def refresh_fondy_order_id(self):
        """Новый order_id перед повторной попыткой оплаты у Fondy (старый,
        неуспешный, переиспользовать нельзя)."""
        self.fondy_order_id = _generate_order_id(self.application)
        self.save(update_fields=["fondy_order_id"])
