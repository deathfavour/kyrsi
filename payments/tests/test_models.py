from decimal import Decimal

from payments.models import Payment


def test_get_or_init_creates_snapshot(application):
    payment, created = Payment.objects.get_or_init_for_application(application)
    assert created is True
    assert payment.course_price == Decimal("405.00")  # training_center_price_usd (MMTC)
    assert payment.commission_amount == Decimal("45.00")  # price_usd - training_center_price_usd
    assert payment.total_amount == Decimal("450.00")  # price_usd — what the candidate pays
    assert payment.status == Payment.Status.PENDING
    assert payment.fondy_order_id
    assert payment.invoice_number


def test_get_or_init_is_idempotent(application):
    payment1, created1 = Payment.objects.get_or_init_for_application(application)
    payment2, created2 = Payment.objects.get_or_init_for_application(application)
    assert created1 is True
    assert created2 is False
    assert payment1.pk == payment2.pk


def test_price_change_after_creation_does_not_affect_snapshot(application, course):
    payment, _ = Payment.objects.get_or_init_for_application(application)
    course.price_usd = Decimal("999.00")
    course.save(update_fields=["price_usd"])
    payment.refresh_from_db()
    assert payment.course_price == Decimal("405.00")


def test_refresh_fondy_order_id_changes_value(application):
    payment, _ = Payment.objects.get_or_init_for_application(application)
    old_order_id = payment.fondy_order_id
    payment.refresh_fondy_order_id()
    payment.refresh_from_db()
    assert payment.fondy_order_id != old_order_id


def test_payment_str(application):
    payment, _ = Payment.objects.get_or_init_for_application(application)
    assert str(payment) == f"{payment.invoice_number} — John Seaman"
