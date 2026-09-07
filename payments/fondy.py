import hashlib
import hmac
import json

import requests
from django.conf import settings

CHECKOUT_URL_ENDPOINT = "https://api.fondy.eu/api/checkout/url/"
REVERSE_ENDPOINT = "https://api.fondy.eu/api/reverse/order_id/"


class FondyError(Exception):
    pass


def _to_cents(amount) -> int:
    return int((amount * 100).to_integral_value())


def _signature(params: dict) -> str:
    """Fondy: sha1('secret_key|value1|value2|...'), значения отсортированы по
    ключу, пустые и сам 'signature' исключены."""
    values = [
        str(v) for key, v in sorted(params.items()) if key != "signature" and v not in (None, "")
    ]
    raw = "|".join([settings.FONDY_SECRET_KEY, *values])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _build_split_rules(payment) -> list:
    """Разбивка одного платежа между учебным центром и партнёром (Fondy Split
    Payments, оба — submerchants после KYB).

    ⚠️ Точные названия полей ниже (receiver_id/amount) нужно сверить с
    аккаунт-менеджером Fondy на первом реальном тестовом платеже — KYB и
    submerchant-регистрация ещё не пройдены (см. CLAUDE.md, шаг 0).
    """
    training_center = payment.application.course.training_center
    return [
        {
            "receiver_id": training_center.fondy_receiver_id,
            "amount": _to_cents(payment.course_price),
        },
        {
            "receiver_id": settings.FONDY_PARTNER_RECEIVER_ID,
            "amount": _to_cents(payment.commission_amount),
        },
    ]


def create_checkout_url(payment, server_callback_url: str, response_url: str) -> str:
    params = {
        "order_id": payment.fondy_order_id,
        "merchant_id": settings.FONDY_MERCHANT_ID,
        "order_desc": f"{payment.application.course.title} ({payment.invoice_number})",
        "amount": str(_to_cents(payment.total_amount)),
        "currency": payment.currency.upper(),
        "server_callback_url": server_callback_url,
        "response_url": response_url,
        "split_rules": json.dumps(_build_split_rules(payment)),
    }
    params["signature"] = _signature(params)

    response = requests.post(CHECKOUT_URL_ENDPOINT, json={"request": params}, timeout=15)
    response.raise_for_status()
    payload = response.json().get("response", {})

    if payload.get("response_status") != "success":
        raise FondyError(payload.get("error_message") or "Fondy checkout creation failed")

    return payload["checkout_url"]


def refund_payment(payment, amount=None) -> dict:
    """Fondy Reverse API — возврат по order_id уже оплаченного заказа.

    Вызывается только вручную из admin (см. RefundRequestAdmin), не
    автоматически при создании RefundRequest (см. CLAUDE.md "Модуль возврата").
    `amount` — частичный возврат в валюте платежа; по умолчанию total_amount
    (полный возврат).

    ⚠️ Как и split_rules, точный формат ответа Reverse API не подтверждён на
    реальном тестовом платеже (KYB не пройден, см. CLAUDE.md шаг 0) — сверить
    с аккаунт-менеджером Fondy при первой реальной интеграции.
    """
    refund_amount = amount if amount is not None else payment.total_amount
    params = {
        "order_id": payment.fondy_order_id,
        "merchant_id": settings.FONDY_MERCHANT_ID,
        "amount": str(_to_cents(refund_amount)),
        "currency": payment.currency.upper(),
    }
    params["signature"] = _signature(params)

    response = requests.post(REVERSE_ENDPOINT, json={"request": params}, timeout=15)
    response.raise_for_status()
    payload = response.json().get("response", {})

    if payload.get("response_status") != "success":
        raise FondyError(payload.get("error_message") or "Fondy refund failed")

    return payload


def verify_signature(data: dict) -> bool:
    received = data.get("signature", "")
    if not received:
        return False
    expected = _signature({k: v for k, v in data.items() if k != "signature"})
    return hmac.compare_digest(received, expected)
