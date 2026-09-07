from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from notifications.services import (
    notify_accounting_paid,
    notify_candidate_paid,
    notify_partner_paid,
    notify_refund_requested,
    notify_support_ticket_created,
    notify_training_center_paid,
)

FAKE_PDF = b"%PDF-fake%"


@pytest.fixture
def paid_payment(payment, settings):
    settings.PARTNER_NOTIFICATION_EMAIL = "partner@example.com"
    settings.ACCOUNTING_EMAIL = "accounting@example.com"
    payment.paid_at = timezone.now()
    payment.save(update_fields=["paid_at"])
    return payment


def test_notify_candidate_paid_sends_invoice_with_attachment(paid_payment, application, course):
    notify_candidate_paid(application, paid_payment, course, FAKE_PDF)

    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == [application.email]
    assert paid_payment.invoice_number in sent.subject
    assert sent.attachments == [
        (f"{paid_payment.invoice_number}-invoice.pdf", FAKE_PDF, "application/pdf")
    ]


def test_notify_candidate_paid_adds_weekend_note_on_saturday(paid_payment, application, course):
    saturday = timezone.datetime(2026, 7, 4, 12, 0, tzinfo=timezone.get_current_timezone())
    paid_payment.paid_at = saturday
    paid_payment.save(update_fields=["paid_at"])

    notify_candidate_paid(application, paid_payment, course, FAKE_PDF)

    assert "первый рабочий день" in mail.outbox[0].body


def test_notify_candidate_paid_no_weekend_note_on_weekday(paid_payment, application, course):
    monday = timezone.datetime(2026, 7, 6, 12, 0, tzinfo=timezone.get_current_timezone())
    paid_payment.paid_at = monday
    paid_payment.save(update_fields=["paid_at"])

    notify_candidate_paid(application, paid_payment, course, FAKE_PDF)

    assert "первый рабочий день" not in mail.outbox[0].body


def test_notify_training_center_paid_sends_to_contact_email(
    paid_payment, application, course, training_center
):
    notify_training_center_paid(application, paid_payment, course, training_center, FAKE_PDF)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [training_center.contact_email]
    assert application.full_name in mail.outbox[0].body


@patch("notifications.services._telegram_backend.send_message")
def test_notify_partner_paid_sends_email_and_telegram(
    mock_telegram, paid_payment, course, settings
):
    notify_partner_paid(paid_payment, course, FAKE_PDF)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["partner@example.com"]
    mock_telegram.assert_called_once()
    assert course.title in mock_telegram.call_args[0][0]


def test_notify_accounting_paid_sends_summary_without_attachment(paid_payment, course, settings):
    notify_accounting_paid(paid_payment, course)

    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ["accounting@example.com"]
    assert sent.attachments == []


def test_notify_refund_requested_emails_training_center_partner_and_accounting(
    paid_payment, application, course, training_center, settings
):
    from refunds.models import RefundRequest

    refund_request = RefundRequest.objects.create(
        payment=paid_payment, reason="Course no longer needed."
    )

    notify_refund_requested(refund_request)

    assert len(mail.outbox) == 3
    recipients = {sent.to[0] for sent in mail.outbox}
    assert recipients == {
        training_center.contact_email,
        "partner@example.com",
        "accounting@example.com",
    }
    for sent in mail.outbox:
        assert paid_payment.invoice_number in sent.subject


def test_notify_support_ticket_created_question_notifies_partner_only(db, settings):
    from support.models import SupportTicket

    settings.PARTNER_NOTIFICATION_EMAIL = "partner@example.com"
    ticket = SupportTicket.objects.create(
        ticket_type=SupportTicket.TicketType.QUESTION,
        applicant_name="Jane Seafarer",
        applicant_email="jane@example.com",
        message="How long does the course take?",
    )

    notify_support_ticket_created(ticket)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["partner@example.com"]


def test_notify_support_ticket_created_refund_request_notifies_all_three(
    paid_payment, training_center, settings
):
    from support.models import SupportTicket

    settings.PARTNER_NOTIFICATION_EMAIL = "partner@example.com"
    settings.ACCOUNTING_EMAIL = "accounting@example.com"
    ticket = SupportTicket.objects.create(
        ticket_type=SupportTicket.TicketType.REFUND_REQUEST,
        applicant_name="Jane Seafarer",
        applicant_email="jane@example.com",
        related_payment=paid_payment,
        message="I'd like a refund.",
    )

    notify_support_ticket_created(ticket)

    assert len(mail.outbox) == 3
    recipients = {sent.to[0] for sent in mail.outbox}
    assert recipients == {
        training_center.contact_email,
        "partner@example.com",
        "accounting@example.com",
    }
