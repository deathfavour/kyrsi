from django.core import mail
from django.urls import reverse

from refunds.models import RefundRequest


def test_get_request_refund_renders_form(client, db):
    response = client.get(reverse("refunds:request_refund"))
    assert response.status_code == 200
    assert b"Invoice Number" in response.content


def test_post_valid_data_creates_refund_request_and_notifies(client, paid_payment, settings):
    settings.PARTNER_NOTIFICATION_EMAIL = "partner@example.com"
    settings.ACCOUNTING_EMAIL = "accounting@example.com"

    response = client.post(reverse("refunds:request_refund"), data={
        "invoice_number": paid_payment.invoice_number,
        "email": paid_payment.application.email,
        "reason": "Course no longer needed.",
    })

    assert response.status_code == 200
    assert RefundRequest.objects.count() == 1
    assert len(mail.outbox) == 3  # training center, partner, accounting


def test_post_invalid_data_rerenders_form_with_errors(client, db):
    response = client.post(reverse("refunds:request_refund"), data={
        "invoice_number": "INV-MISSING",
        "email": "nobody@example.com",
        "reason": "Test.",
    })

    assert response.status_code == 200
    assert RefundRequest.objects.count() == 0
    assert b"couldn" in response.content
