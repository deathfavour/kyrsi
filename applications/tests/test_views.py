import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from applications.models import Application
from courses.models import Course, TrainingCenter

HTMX_HEADERS = {"HTTP_HX_REQUEST": "true"}


def _required_documents():
    return {
        "seamans_book": SimpleUploadedFile("seamans_book.pdf", b"%PDF-1.4 fake", "application/pdf"),
        "certificate_of_competency": SimpleUploadedFile(
            "coc.pdf", b"%PDF-1.4 fake", "application/pdf"
        ),
    }


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
        training_center_price_usd="405.00",
        commission_percent="10.00",
    )


VALID_APPLICATION_DATA = {
    "full_name": "John Seaman",
    "date_of_birth": "1990-01-01",
    "citizenship": "Georgia",
    "position": "Able Seafarer",
    "company": "",
    "phone": "+995500000000",
    "email": "john@example.com",
    "comments": "",
}

ALL_AGREED = {
    "agree_purchase_terms": "on",
    "agree_refund_policy": "on",
    "agree_gdpr": "on",
    "agree_representative": "on",
}


def test_step2_get_form_404_for_course_without_price(client, training_center):
    unpriced_course = Course.objects.create(
        training_center=training_center,
        slug="unpriced-course",
        title="Unpriced Course",
        description="Pricing not published yet.",
        duration="4 hours",
        commission_percent="10.00",
        is_active=True,
    )
    url = reverse("applications:apply_form", args=[unpriced_course.slug])
    response = client.get(url)
    assert response.status_code == 404


def test_step1_course_page_links_to_apply_form(client, course):
    response = client.get(reverse("courses:course_detail", args=[course.slug]))
    assert response.status_code == 200
    assert reverse("applications:apply_form", args=[course.slug]) in response.content.decode()


def test_step2_get_form_full_page(client, course):
    response = client.get(reverse("applications:apply_form", args=[course.slug]))
    assert response.status_code == 200
    assert "APPLICATION FORM" in response.content.decode()


def test_step2_post_creates_application_and_returns_confirm_step(client, course):
    url = reverse("applications:apply_form", args=[course.slug])
    data = {**VALID_APPLICATION_DATA, **_required_documents()}
    response = client.post(url, data, **HTMX_HEADERS)
    assert response.status_code == 200
    assert Application.objects.count() == 1
    application = Application.objects.get()
    assert application.course == course
    assert application.agreed_terms_at is None
    assert "PLEASE REVIEW AND CONFIRM" in response.content.decode()
    assert application.documents.count() == 2


def test_step2_missing_required_document_reshows_form_without_creating_application(
    client, course
):
    url = reverse("applications:apply_form", args=[course.slug])
    data = {**VALID_APPLICATION_DATA, "seamans_book": _required_documents()["seamans_book"]}
    response = client.post(url, data, **HTMX_HEADERS)
    assert response.status_code == 200
    assert Application.objects.count() == 0
    assert "APPLICATION FORM" in response.content.decode()


def test_step2_invalid_data_reshows_form_without_creating_application(client, course):
    url = reverse("applications:apply_form", args=[course.slug])
    data = {**VALID_APPLICATION_DATA, **_required_documents(), "email": "not-an-email"}
    response = client.post(url, data, **HTMX_HEADERS)
    assert response.status_code == 200
    assert Application.objects.count() == 0
    assert "APPLICATION FORM" in response.content.decode()


def test_step3_all_boxes_checked_stamps_agreed_terms_at_and_moves_to_payment(client, course):
    client.post(
        reverse("applications:apply_form", args=[course.slug]),
        {**VALID_APPLICATION_DATA, **_required_documents()},
    )
    application = Application.objects.get()

    url = reverse("applications:apply_confirm", args=[course.slug, application.pk])
    response = client.post(url, ALL_AGREED, follow=True, **HTMX_HEADERS)

    application.refresh_from_db()
    assert response.status_code == 200
    assert application.agreed_terms_at is not None
    assert "PAYMENT DETAILS" in response.content.decode()
    assert "Pay Securely Now" in response.content.decode()


@pytest.mark.parametrize("missing_field", list(ALL_AGREED.keys()))
def test_step3_missing_any_checkbox_does_not_stamp_agreement(client, course, missing_field):
    client.post(
        reverse("applications:apply_form", args=[course.slug]),
        {**VALID_APPLICATION_DATA, **_required_documents()},
    )
    application = Application.objects.get()

    incomplete = {k: v for k, v in ALL_AGREED.items() if k != missing_field}
    url = reverse("applications:apply_confirm", args=[course.slug, application.pk])
    response = client.post(url, incomplete, **HTMX_HEADERS)

    application.refresh_from_db()
    assert response.status_code == 200
    assert application.agreed_terms_at is None
    assert "PLEASE REVIEW AND CONFIRM" in response.content.decode()


def test_step4_payment_page_requires_confirmed_terms(client, course):
    client.post(
        reverse("applications:apply_form", args=[course.slug]),
        {**VALID_APPLICATION_DATA, **_required_documents()},
    )
    application = Application.objects.get()

    url = reverse("applications:apply_payment", args=[course.slug, application.pk])
    response = client.get(url)
    assert response.status_code == 404

    application.agreed_terms_at = "2026-07-01T12:00:00Z"
    application.save(update_fields=["agreed_terms_at"])

    response = client.get(url)
    assert response.status_code == 200
    # total_amount = Course.price_usd (450.00) — what the candidate pays, no markup added.
    assert "450.00" in response.content.decode()
