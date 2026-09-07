from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from payments.models import Payment
from payments.tasks import process_paid_payment

FAKE_PDF = b"%PDF-fake%"


@pytest.fixture
def paid_payment(application, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.PARTNER_NOTIFICATION_EMAIL = "partner@example.com"
    settings.ACCOUNTING_EMAIL = "accounting@example.com"

    payment, _ = Payment.objects.get_or_init_for_application(application)
    payment.status = Payment.Status.PAID
    payment.paid_at = timezone.now()
    payment.save(update_fields=["status", "paid_at"])
    return payment


@patch("notifications.services._telegram_backend.send_message")
@patch("payments.tasks.html_to_pdf", return_value=FAKE_PDF)
def test_process_paid_payment_sends_four_emails(mock_pdf, mock_telegram, paid_payment):
    process_paid_payment(paid_payment.pk)

    assert len(mail.outbox) == 4
    recipients = {msg.to[0] for msg in mail.outbox}
    training_center = paid_payment.application.course.training_center
    assert recipients == {
        paid_payment.application.email,
        training_center.contact_email,
        "partner@example.com",
        "accounting@example.com",
    }
    mock_telegram.assert_called_once()

    paid_payment.refresh_from_db()
    assert paid_payment.candidate_invoice_pdf.name
    assert paid_payment.training_center_confirmation_pdf.name
    assert paid_payment.partner_invoice_pdf.name


@patch("notifications.services._telegram_backend.send_message")
@patch("payments.tasks.html_to_pdf", return_value=FAKE_PDF)
def test_weekend_note_added_on_saturday(mock_pdf, mock_telegram, paid_payment):
    saturday = datetime(2026, 7, 4, 12, 0, tzinfo=dt_timezone.utc)  # 2026-07-04 is a Saturday
    paid_payment.paid_at = saturday
    paid_payment.save(update_fields=["paid_at"])

    process_paid_payment(paid_payment.pk)

    candidate_email = next(m for m in mail.outbox if m.to[0] == paid_payment.application.email)
    assert "первый рабочий день" in candidate_email.body


@patch("notifications.services._telegram_backend.send_message")
@patch("payments.tasks.html_to_pdf", return_value=FAKE_PDF)
def test_no_weekend_note_on_weekday(mock_pdf, mock_telegram, paid_payment):
    monday = datetime(2026, 7, 6, 12, 0, tzinfo=dt_timezone.utc)  # 2026-07-06 is a Monday
    paid_payment.paid_at = monday
    paid_payment.save(update_fields=["paid_at"])

    process_paid_payment(paid_payment.pk)

    candidate_email = next(m for m in mail.outbox if m.to[0] == paid_payment.application.email)
    assert "первый рабочий день" not in candidate_email.body


@patch("payments.tasks.html_to_pdf", side_effect=RuntimeError("PDF backend unavailable"))
def test_process_paid_payment_logs_and_reraises_on_failure(mock_pdf, paid_payment, caplog):
    """fondy_webhook calls this task via apply_async() without .get() — any
    exception here would otherwise vanish silently (found during an end-to-end
    golden-path check). Confirms the failure is at least logged before
    propagating, so retries/monitoring have something to act on."""
    with pytest.raises(RuntimeError):
        process_paid_payment(paid_payment.pk)

    assert any(
        "process_paid_payment raised" in record.message and str(paid_payment.pk) in record.message
        for record in caplog.records
    )
    assert len(mail.outbox) == 0
