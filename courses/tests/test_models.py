import pytest

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


def test_training_center_str(training_center):
    assert str(training_center) == "Batumi Maritime Training Center"


def test_training_center_defaults(training_center):
    assert training_center.currency == "USD"
    assert training_center.is_active is True


def test_course_str(course):
    assert str(course) == "Basic Safety Training"


def test_course_linked_to_training_center(course, training_center):
    assert course.training_center == training_center
    assert course in training_center.courses.all()


def test_course_has_price_true_when_price_set(course):
    assert course.has_price is True


def test_course_has_price_false_when_price_missing(training_center):
    course = Course.objects.create(
        training_center=training_center,
        slug="tbd-price-course",
        title="TBD Price Course",
        description="Pricing not published yet.",
        duration="4 hours",
        commission_percent="10.00",
    )
    assert course.price_usd is None
    assert course.has_price is False
