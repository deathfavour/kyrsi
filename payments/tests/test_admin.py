from io import BytesIO

import pytest
from django.contrib.admin.sites import AdminSite
from openpyxl import load_workbook

from payments.admin import PaymentAdmin
from payments.models import Payment


@pytest.fixture
def payment(application):
    payment, _ = Payment.objects.get_or_init_for_application(application)
    return payment


def test_export_to_excel_returns_xlsx_with_payment_row(payment):
    admin = PaymentAdmin(Payment, AdminSite())

    response = admin.export_to_excel(None, Payment.objects.filter(pk=payment.pk))

    workbook = load_workbook(BytesIO(response.content))
    sheet = workbook.active
    assert sheet["A1"].value == "Invoice Number"
    assert sheet["A2"].value == payment.invoice_number
