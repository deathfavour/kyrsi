import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

from notifications.services import (
    notify_accounting_paid,
    notify_candidate_paid,
    notify_partner_paid,
    notify_training_center_paid,
)

from .models import Payment
from .pdf import html_to_pdf

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def process_paid_payment(payment_id):
    """Через 15 минут после оплаты (см. вызов в payments.views.fondy_webhook):
    генерирует PDF-документы и уведомляет кандидата, учебный центр, партнёра
    и бухгалтерию.

    `fondy_webhook` вызывает это через `apply_async()` без `.get()`, поэтому
    любая ошибка здесь была бы молча потеряна — не видна в HTTP-ответе на
    webhook и никак не сигнализирована (найдено при сквозной проверке golden
    path: WeasyPrint-сбой в этом Windows-окружении проходил незамеченным,
    webhook всё равно отвечал Fondy "OK"). `autoretry_for` даёт транзиентным
    сбоям (email/PDF-рендер временно недоступны) до 5 повторов с backoff;
    финальный отказ после исчерпания попыток — logger.exception ниже, чтобы
    он хотя бы попадал в логи/мониторинг, а не пропадал бесследно."""
    try:
        payment = Payment.objects.select_related(
            "application", "application__course", "application__course__training_center"
        ).get(pk=payment_id)
        application = payment.application
        course = application.course
        training_center = course.training_center

        context = {
            "payment": payment,
            "application": application,
            "course": course,
            "training_center": training_center,
        }

        candidate_pdf = html_to_pdf(
            render_to_string("payments/pdf/candidate_invoice.html", context)
        )
        training_center_pdf = html_to_pdf(
            render_to_string("payments/pdf/training_center_confirmation.html", context)
        )
        partner_pdf = html_to_pdf(render_to_string("payments/pdf/partner_invoice.html", context))

        payment.candidate_invoice_pdf.save(
            f"{payment.invoice_number}-candidate.pdf", ContentFile(candidate_pdf), save=False
        )
        payment.training_center_confirmation_pdf.save(
            f"{payment.invoice_number}-training-center.pdf",
            ContentFile(training_center_pdf),
            save=False,
        )
        payment.partner_invoice_pdf.save(
            f"{payment.invoice_number}-partner.pdf", ContentFile(partner_pdf), save=False
        )
        payment.save(
            update_fields=[
                "candidate_invoice_pdf",
                "training_center_confirmation_pdf",
                "partner_invoice_pdf",
            ]
        )

        notify_candidate_paid(application, payment, course, candidate_pdf)
        notify_training_center_paid(
            application, payment, course, training_center, training_center_pdf
        )
        notify_partner_paid(payment, course, partner_pdf)
        notify_accounting_paid(payment, course)
    except Exception:
        logger.exception(
            "process_paid_payment raised for payment_id=%s — will retry per "
            "autoretry_for unless retries are exhausted, in which case PDFs/"
            "notifications for this payment are left incomplete",
            payment_id,
        )
        raise
