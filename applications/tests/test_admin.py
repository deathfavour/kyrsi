import datetime
from io import BytesIO

import pytest
from django.contrib.admin.sites import AdminSite
from openpyxl import load_workbook

from applications.admin import ApplicationAdmin
from applications.models import Application
from courses.models import Course, TrainingCenter


@pytest.fixture
def training_center(db):
    return TrainingCenter.objects.create(
        name="Batumi Maritime Training Center",
        bank_name="TBC Bank Georgia",
        bank_country="Georgia",
        account_number="GE00TB0000000000000000",
        swift="TBCBGE22",
        contact_email="office@batumi-mtc.example",
    )


@pytest.fixture
def course(training_center):
    return Course.objects.create(
        training_center=training_center,
        slug="basic-safety-training",
        title="Basic Safety Training",
        description="STCW basic safety training course.",
        duration="5 days",
        price_usd="450.00",
        commission_percent="10.00",
    )


@pytest.fixture
def application(course):
    return Application.objects.create(
        course=course,
        full_name="John Seaman",
        date_of_birth=datetime.date(1990, 1, 1),
        citizenship="Georgia",
        position="Able Seafarer",
        phone="+995500000000",
        email="john@example.com",
    )


def test_export_to_excel_returns_xlsx_with_application_row(application):
    admin = ApplicationAdmin(Application, AdminSite())

    response = admin.export_to_excel(None, Application.objects.filter(pk=application.pk))

    workbook = load_workbook(BytesIO(response.content))
    sheet = workbook.active
    assert sheet["A1"].value == "Full Name"
    assert sheet["A2"].value == "John Seaman"
    assert sheet["B2"].value == "Basic Safety Training"
