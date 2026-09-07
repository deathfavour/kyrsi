from payments.models import Payment
from refunds.forms import RefundRequestForm


def test_form_valid_finds_matching_payment(paid_payment):
    form = RefundRequestForm(data={
        "invoice_number": paid_payment.invoice_number,
        "email": paid_payment.application.email,
        "reason": "Course no longer needed.",
    })
    assert form.is_valid(), form.errors
    assert form.cleaned_data["payment"] == paid_payment


def test_form_invalid_when_no_matching_payment(db):
    form = RefundRequestForm(data={
        "invoice_number": "INV-DOES-NOT-EXIST",
        "email": "nobody@example.com",
        "reason": "Test.",
    })
    assert not form.is_valid()
    assert "couldn" in str(form.errors) and "find a payment" in str(form.errors)


def test_form_invalid_when_payment_not_paid(application):
    payment, _ = Payment.objects.get_or_init_for_application(application)
    form = RefundRequestForm(data={
        "invoice_number": payment.invoice_number,
        "email": application.email,
        "reason": "Test.",
    })
    assert not form.is_valid()
    assert "completed payments" in str(form.errors)


def test_form_save_creates_refund_request(paid_payment):
    form = RefundRequestForm(data={
        "invoice_number": paid_payment.invoice_number,
        "email": paid_payment.application.email,
        "reason": "Course no longer needed.",
    })
    assert form.is_valid()
    refund_request = form.save()
    assert refund_request.payment == paid_payment
    assert refund_request.reason == "Course no longer needed."
