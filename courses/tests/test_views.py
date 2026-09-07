import pytest
from django.urls import reverse

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
def active_course(training_center):
    return Course.objects.create(
        training_center=training_center,
        slug="basic-safety-training",
        title="Basic Safety Training",
        description="STCW basic safety training course.",
        duration="5 days",
        price_usd="450.00",
        commission_percent="10.00",
        is_active=True,
    )


@pytest.fixture
def inactive_course(training_center):
    return Course.objects.create(
        training_center=training_center,
        slug="archived-course",
        title="Archived Course",
        description="No longer offered.",
        duration="3 days",
        price_usd="300.00",
        commission_percent="10.00",
        is_active=False,
    )


def test_home_page_loads(client):
    response = client.get(reverse("courses:home"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Garant United Academy" in html
    assert "hero-cargo-tanker.jpg" in html


def test_course_list_shows_active_courses(client, active_course, inactive_course):
    response = client.get(reverse("courses:course_list"))
    assert response.status_code == 200
    assert active_course.title in response.content.decode()
    assert inactive_course.title not in response.content.decode()


def test_course_detail_returns_active_course(client, active_course):
    url = reverse("courses:course_detail", args=[active_course.slug])
    response = client.get(url)
    assert response.status_code == 200
    assert active_course.title in response.content.decode()


def test_course_detail_404_for_inactive_course(client, inactive_course):
    url = reverse("courses:course_detail", args=[inactive_course.slug])
    response = client.get(url)
    assert response.status_code == 404


@pytest.fixture
def unpriced_course(training_center):
    return Course.objects.create(
        training_center=training_center,
        slug="unpriced-course",
        title="Unpriced Course",
        description="Pricing not published yet.",
        duration="4 hours",
        commission_percent="10.00",
        is_active=True,
    )


def test_course_list_shows_contact_us_for_unpriced_course(client, unpriced_course):
    response = client.get(reverse("courses:course_list"))
    assert response.status_code == 200
    content = response.content.decode()
    assert unpriced_course.title in content
    assert "Contact us" in content


def test_course_detail_shows_contact_us_and_hides_apply_link(client, unpriced_course):
    url = reverse("courses:course_detail", args=[unpriced_course.slug])
    response = client.get(url)
    content = response.content.decode()
    assert response.status_code == 200
    assert "Contact us for price" in content
    assert "Apply now" not in content
