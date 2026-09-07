from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from payments.fondy import _signature
from payments.models import Payment


@pytest.fixture
def confirmed_application(application):
    application.agreed_terms_at = timezone.now()
    application.save(update_fields=["agreed_terms_at"])
    return application


def _signed_webhook_payload(payment, order_status, settings):
    settings.FONDY_SECRET_KEY = "secret"
    data = {"order_id": payment.fondy_order_id, "order_status": order_status}
    data["signature"] = _signature(data)
    return data


@patch("payments.views.fondy.create_checkout_url")
def test_initiate_redirects_to_fondy_checkout(
    mock_create_url, client, course, confirmed_application
):
    mock_create_url.return_value = "https://pay.fondy.eu/checkout/xyz"
    url = reverse("payments:initiate", args=[course.slug, confirmed_application.pk])

    response = client.post(url)

    assert response.status_code == 302
    assert response.url == "https://pay.fondy.eu/checkout/xyz"
    assert Payment.objects.filter(application=confirmed_application).exists()


def test_initiate_requires_confirmed_terms(client, course, application):
    url = reverse("payments:initiate", args=[course.slug, application.pk])
    response = client.post(url)
    assert response.status_code == 404


def test_initiate_get_not_allowed(client, course, confirmed_application):
    url = reverse("payments:initiate", args=[course.slug, confirmed_application.pk])
    response = client.get(url)
    assert response.status_code == 405


@patch("payments.views.process_paid_payment.apply_async")
def test_webhook_approved_marks_paid_and_queues_task(
    mock_apply_async, client, settings, confirmed_application
):
    payment, _ = Payment.objects.get_or_init_for_application(confirmed_application)
    data = _signed_webhook_payload(payment, "approved", settings)

    response = client.post(reverse("payments:fondy_webhook"), data)

    payment.refresh_from_db()
    assert response.status_code == 200
    assert payment.status == Payment.Status.PAID
    assert payment.paid_at is not None
    mock_apply_async.assert_called_once_with(args=[payment.pk], countdown=15 * 60)


def test_webhook_invalid_signature_rejected(client, settings, confirmed_application):
    settings.FONDY_SECRET_KEY = "secret"
    payment, _ = Payment.objects.get_or_init_for_application(confirmed_application)
    data = {"order_id": payment.fondy_order_id, "order_status": "approved", "signature": "wrong"}

    response = client.post(reverse("payments:fondy_webhook"), data)

    payment.refresh_from_db()
    assert response.status_code == 403
    assert payment.status == Payment.Status.PENDING


def test_webhook_unknown_order_id_404(client, settings, db):
    settings.FONDY_SECRET_KEY = "secret"
    data = {"order_id": "does-not-exist", "order_status": "approved"}
    data["signature"] = _signature(data)

    response = client.post(reverse("payments:fondy_webhook"), data)
    assert response.status_code == 404


def test_webhook_declined_marks_failed(client, settings, confirmed_application):
    payment, _ = Payment.objects.get_or_init_for_application(confirmed_application)
    data = _signed_webhook_payload(payment, "declined", settings)

    response = client.post(reverse("payments:fondy_webhook"), data)

    payment.refresh_from_db()
    assert response.status_code == 200
    assert payment.status == Payment.Status.FAILED


def test_success_page_renders(client, confirmed_application, course):
    Payment.objects.get_or_init_for_application(confirmed_application)
    url = reverse("payments:success", args=[course.slug, confirmed_application.pk])

    response = client.get(url)
    assert response.status_code == 200
