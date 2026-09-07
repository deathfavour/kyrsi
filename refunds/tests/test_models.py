from refunds.models import RefundRequest


def test_refund_request_default_status_is_pending(paid_payment):
    refund_request = RefundRequest.objects.create(payment=paid_payment, reason="Changed plans.")
    assert refund_request.status == RefundRequest.Status.PENDING
    assert refund_request.resolved_at is None
    assert refund_request.resolved_by is None


def test_refund_request_str(paid_payment):
    refund_request = RefundRequest.objects.create(payment=paid_payment, reason="Changed plans.")
    assert paid_payment.invoice_number in str(refund_request)
