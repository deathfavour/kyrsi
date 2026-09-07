from unittest.mock import MagicMock, patch

import pytest

from payments import fondy
from payments.models import Payment


@pytest.fixture
def payment(application):
    payment, _ = Payment.objects.get_or_init_for_application(application)
    return payment


def test_signature_roundtrip(settings):
    settings.FONDY_SECRET_KEY = "test-secret"
    params = {"order_id": "abc", "amount": "1000", "currency": "USD"}
    signed = dict(params)
    signed["signature"] = fondy._signature(params)
    assert fondy.verify_signature(signed) is True


def test_signature_rejects_tampering(settings):
    settings.FONDY_SECRET_KEY = "test-secret"
    params = {"order_id": "abc", "amount": "1000"}
    signed = dict(params)
    signed["signature"] = fondy._signature(params)
    signed["amount"] = "9999"
    assert fondy.verify_signature(signed) is False


def test_verify_signature_missing_signature_is_rejected():
    assert fondy.verify_signature({"order_id": "abc"}) is False


def test_build_split_rules_amounts_in_cents(payment, settings):
    settings.FONDY_PARTNER_RECEIVER_ID = "PARTNER-1"
    rules = fondy._build_split_rules(payment)
    training_center = payment.application.course.training_center
    assert rules[0]["receiver_id"] == training_center.fondy_receiver_id
    assert rules[0]["amount"] == 40500  # course_price 405.00 -> cents
    assert rules[1]["receiver_id"] == "PARTNER-1"
    assert rules[1]["amount"] == 4500  # commission_amount 45.00 -> cents


@patch("payments.fondy.requests.post")
def test_create_checkout_url_success(mock_post, payment, settings):
    settings.FONDY_MERCHANT_ID = "1"
    settings.FONDY_SECRET_KEY = "secret"
    settings.FONDY_PARTNER_RECEIVER_ID = "PARTNER-1"

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "response": {"response_status": "success", "checkout_url": "https://pay.fondy.eu/xyz"}
    }
    mock_post.return_value = mock_response

    url = fondy.create_checkout_url(
        payment,
        server_callback_url="https://example.com/webhook/",
        response_url="https://example.com/success/",
    )

    assert url == "https://pay.fondy.eu/xyz"
    sent_payload = mock_post.call_args.kwargs["json"]["request"]
    assert sent_payload["order_id"] == payment.fondy_order_id
    assert sent_payload["amount"] == "45000"  # total_amount 450.00 -> cents
    assert "signature" in sent_payload


@patch("payments.fondy.requests.post")
def test_create_checkout_url_failure_raises(mock_post, payment, settings):
    settings.FONDY_SECRET_KEY = "secret"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "response": {"response_status": "failure", "error_message": "bad order"}
    }
    mock_post.return_value = mock_response

    with pytest.raises(fondy.FondyError):
        fondy.create_checkout_url(
            payment, server_callback_url="https://x.example/", response_url="https://y.example/"
        )
