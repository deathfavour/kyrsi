from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from openpyxl import load_workbook

from payments.fondy import FondyError
from payments.models import Payment
from refunds.admin import RefundRequestAdmin
from refunds.models import RefundRequest


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )


@pytest.fixture
def refund_request(paid_payment):
    return RefundRequest.objects.create(payment=paid_payment, reason="Test reason.")


@pytest.fixture
def admin_request(admin_user):
    request = RequestFactory().post("/admin/refunds/refundrequest/")
    request.user = admin_user
    # messages framework needs this on the request in admin actions
    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "session", {})
    setattr(request, "_messages", FallbackStorage(request))
    return request


@patch("refunds.admin.fondy.refund_payment")
def test_approve_and_process_refund_marks_completed(mock_refund, admin_request, refund_request):
    mock_refund.return_value = {"response_status": "success"}
    admin = RefundRequestAdmin(RefundRequest, AdminSite())

    admin.approve_and_process_refund(
        admin_request, RefundRequest.objects.filter(pk=refund_request.pk)
    )

    refund_request.refresh_from_db()
    assert refund_request.status == RefundRequest.Status.COMPLETED
    assert refund_request.resolved_by == admin_request.user
    assert refund_request.resolved_at is not None

    refund_request.payment.refresh_from_db()
    assert refund_request.payment.status == Payment.Status.REFUNDED
    mock_refund.assert_called_once_with(refund_request.payment)


@patch("refunds.admin.fondy.refund_payment")
def test_approve_and_process_refund_handles_fondy_error(
    mock_refund, admin_request, refund_request
):
    mock_refund.side_effect = FondyError("card declined")
    admin = RefundRequestAdmin(RefundRequest, AdminSite())

    admin.approve_and_process_refund(
        admin_request, RefundRequest.objects.filter(pk=refund_request.pk)
    )

    refund_request.refresh_from_db()
    assert refund_request.status == RefundRequest.Status.PENDING


def test_reject_request_marks_rejected(admin_request, refund_request):
    admin = RefundRequestAdmin(RefundRequest, AdminSite())

    admin.reject_request(admin_request, RefundRequest.objects.filter(pk=refund_request.pk))

    refund_request.refresh_from_db()
    assert refund_request.status == RefundRequest.Status.REJECTED
    assert refund_request.resolved_by == admin_request.user


def test_export_to_excel_returns_xlsx_with_refund_row(refund_request):
    admin = RefundRequestAdmin(RefundRequest, AdminSite())

    response = admin.export_to_excel(None, RefundRequest.objects.filter(pk=refund_request.pk))

    workbook = load_workbook(BytesIO(response.content))
    sheet = workbook.active
    assert sheet["A1"].value == "ID"
    assert sheet["C2"].value == refund_request.payment.application.full_name
