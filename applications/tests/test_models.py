import datetime

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from applications.models import Application, ApplicationDocument
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


def test_application_str(application):
    assert str(application) == "John Seaman — Basic Safety Training"


def test_application_agreed_terms_at_null_by_default(application):
    assert application.agreed_terms_at is None


def test_application_linked_to_course(application, course):
    assert application.course == course
    assert application in course.applications.all()


def test_application_document_str(application):
    document = ApplicationDocument.objects.create(
        application=application,
        document_type=ApplicationDocument.SEAMANS_BOOK,
        file=SimpleUploadedFile("seamans_book.pdf", b"%PDF-1.4 fake", "application/pdf"),
    )
    assert str(document) == "Seaman's Book — John Seaman"
    assert document in application.documents.all()


def test_application_document_rejects_disallowed_extension(application):
    document = ApplicationDocument(
        application=application,
        document_type=ApplicationDocument.OTHER,
        file=SimpleUploadedFile("malware.exe", b"fake", "application/octet-stream"),
    )
    with pytest.raises(ValidationError):
        document.full_clean()


def test_application_document_rejects_oversized_file(application):
    oversized_content = b"0" * (5 * 1024 * 1024 + 1)
    document = ApplicationDocument(
        application=application,
        document_type=ApplicationDocument.OTHER,
        file=SimpleUploadedFile("big.pdf", oversized_content, "application/pdf"),
    )
    with pytest.raises(ValidationError):
        document.full_clean()
