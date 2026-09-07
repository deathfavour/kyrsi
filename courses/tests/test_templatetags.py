import pytest

from courses.models import Course, TrainingCenter
from courses.templatetags.course_extras import (
    course_gallery,
    course_hero_image,
    course_thumbnail,
    instructor_portrait,
)


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


def test_unknown_slug_falls_back_to_generic(course):
    course.category = "engineers"
    assert course_thumbnail(course) == "img/course-generic-maritime.jpg"
    assert course_hero_image(course) == "img/course-generic-maritime.jpg"
    assert instructor_portrait(course) == "img/portrait-engineer.jpg"


def test_catalog_slug_uses_unique_file(course):
    course.slug = "man-me-b-c"
    assert course_thumbnail(course) == "img/catalog/man-me-b-c.jpg"
    assert course_hero_image(course) == "img/catalog/man-me-b-c.jpg"
    gallery = course_gallery(course)
    assert gallery[0] == "img/catalog/man-me-b-c.jpg"
    assert len(gallery) == 4
    assert len(set(gallery)) == 4


def test_two_courses_do_not_share_a_thumbnail(training_center):
    a = Course(training_center=training_center, slug="ice-navigation", title="Ice")
    b = Course(training_center=training_center, slug="framo-system", title="Framo")
    assert course_thumbnail(a) != course_thumbnail(b)
    assert course_thumbnail(a) == "img/catalog/ice-navigation.jpg"
    assert course_thumbnail(b) == "img/catalog/framo-system.jpg"
