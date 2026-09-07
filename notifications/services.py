from django.conf import settings
from django.template.loader import render_to_string

from .backends import EmailBackend, TelegramBackend

_email_backend = EmailBackend()
_telegram_backend = TelegramBackend()


def _render_email(template_stem, context):
    text_body = render_to_string(f"notifications/email/{template_stem}.txt", context)
    html_body = render_to_string(f"notifications/email/{template_stem}.html", context)
    return text_body, html_body


def notify_candidate_paid(application, payment, course, invoice_pdf):
    is_weekend = payment.paid_at is not None and payment.paid_at.weekday() >= 5
    context = {
        "payment": payment,
        "application": application,
        "course": course,
        "is_weekend": is_weekend,
    }
    text_body, html_body = _render_email("candidate_payment_confirmation", context)

    _email_backend.send_email(
        subject=f"{course.title} — Invoice {payment.invoice_number}",
        text_body=text_body,
        html_body=html_body,
        to=application.email,
        attachments=[(f"{payment.invoice_number}-invoice.pdf", invoice_pdf)],
    )


def notify_training_center_paid(application, payment, course, training_center, confirmation_pdf):
    context = {"payment": payment, "application": application, "course": course}
    text_body, html_body = _render_email("training_center_new_registration", context)

    _email_backend.send_email(
        subject=f"New paid registration — {application.full_name}",
        text_body=text_body,
        html_body=html_body,
        to=training_center.contact_email,
        attachments=[(f"{payment.invoice_number}-confirmation.pdf", confirmation_pdf)],
    )


def notify_partner_paid(payment, course, commission_pdf):
    context = {"payment": payment, "course": course}
    text_body, html_body = _render_email("partner_commission_invoice", context)

    _email_backend.send_email(
        subject=f"Commission invoice — {payment.invoice_number}",
        text_body=text_body,
        html_body=html_body,
        to=settings.PARTNER_NOTIFICATION_EMAIL,
        attachments=[(f"{payment.invoice_number}-commission.pdf", commission_pdf)],
    )

    _telegram_backend.send_message(
        f"New paid registration: {course.title}. "
        f"Commission: {payment.commission_amount} {payment.currency.upper()}"
    )


def notify_accounting_paid(payment, course):
    context = {"payment": payment, "course": course}
    text_body, html_body = _render_email("accounting_payment_recorded", context)

    _email_backend.send_email(
        subject=f"Payment recorded — {payment.invoice_number}",
        text_body=text_body,
        html_body=html_body,
        to=settings.ACCOUNTING_EMAIL,
    )


def notify_refund_requested(refund_request):
    """Уведомляет учебный центр, партнёра и бухгалтерию о новой заявке на
    возврат (см. CLAUDE.md "Модуль возврата" — "автоматически уведомляются
    все стороны" при создании RefundRequest)."""
    payment = refund_request.payment
    application = payment.application
    course = application.course
    training_center = course.training_center

    context = {
        "refund_request": refund_request,
        "payment": payment,
        "application": application,
        "course": course,
    }
    text_body, html_body = _render_email("refund_requested", context)
    subject = f"Refund requested — {payment.invoice_number}"

    for recipient in (training_center.contact_email, settings.PARTNER_NOTIFICATION_EMAIL,
                       settings.ACCOUNTING_EMAIL):
        _email_backend.send_email(
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            to=recipient,
        )


def notify_support_ticket_created(ticket):
    """Question-тикеты уведомляют только сотрудника поддержки (см. CLAUDE.md
    "Служба поддержки" — "Задать вопрос → ... уведомление сотруднику компании").
    Refund_request-тикеты (созданные из старого Support-флоу без redirect на
    refunds, см. CLAUDE.md "редирект на форму RefundRequest ИЛИ создаёт
    SupportTicket") уведомляют все три стороны, как настоящий RefundRequest."""
    context = {"ticket": ticket}
    text_body, html_body = _render_email("support_ticket_created", context)
    subject = f"New support ticket — {ticket.get_ticket_type_display()}"

    if ticket.ticket_type == ticket.TicketType.REFUND_REQUEST and ticket.related_payment:
        training_center = ticket.related_payment.application.course.training_center
        recipients = (
            training_center.contact_email,
            settings.PARTNER_NOTIFICATION_EMAIL,
            settings.ACCOUNTING_EMAIL,
        )
    else:
        recipients = (settings.PARTNER_NOTIFICATION_EMAIL,)

    for recipient in recipients:
        _email_backend.send_email(
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            to=recipient,
        )
