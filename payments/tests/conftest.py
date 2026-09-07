import datetime

import pytest

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
        fondy_receiver_id="TC-RECEIVER-1",
    )


@pytest.fixture
def course(training_center):
    course = Course.objects.create(
        training_center=training_center,
        slug="basic-safety-training",
        title="Basic Safety Training",
        description="STCW basic safety training course.",
        duration="5 days",
        price_usd="450.00",
        training_center_price_usd="405.00",
        commission_percent="10.00",
    )
    # Refetch so decimal fields come back as Decimal (not the raw str assigned
    # above) — matches how Course is actually read in request handling.
    course.refresh_from_db()
    return course


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
