import pytest
from django.urls import reverse

from author_courses.models import AuthorCourse, CareerPathProgram


@pytest.fixture
def author_course(db):
    return AuthorCourse.objects.create(
        slug="test-author-course",
        title="Test Author Course",
        description="A test course.",
        duration="6 Hours",
        level="intermediate",
        category="navigators",
        price_usd="75.00",
        is_active=True,
    )


@pytest.fixture
def career_path(db):
    return CareerPathProgram.objects.create(
        slug="test-career-path",
        title="Test Career Path",
        description="A test program.",
        duration="40 Hours",
        category="navigators",
        price_usd="120.00",
        is_active=True,
    )


def test_author_course_list_returns_200(client, author_course, career_path):
    response = client.get(reverse("author_courses:author_course_list"))
    assert response.status_code == 200
    assert author_course.title in response.content.decode()
    assert career_path.title in response.content.decode()


def test_author_course_list_excludes_inactive(client, author_course):
    AuthorCourse.objects.create(
        slug="inactive-author-course",
        title="Inactive Author Course",
        duration="6 Hours",
        price_usd="75.00",
        is_active=False,
    )
    response = client.get(reverse("author_courses:author_course_list"))
    assert "Inactive Author Course" not in response.content.decode()


def test_author_course_detail_shows_filled_fields_only(client, author_course):
    author_course.author_name = "Capt. Example"
    author_course.learning_outcomes = "Plan a voyage\n\nUse ECDIS safely\n"
    author_course.save()
    response = client.get(reverse("author_courses:author_course_detail", args=[author_course.slug]))
    content = response.content.decode()
    assert response.status_code == 200
    assert "Capt. Example" in content
    assert "Use ECDIS safely" in content
    assert "Target audience" not in content
    assert "Exclusive program developed by Garant United Academy" in content


def test_author_course_detail_404_for_inactive(client, author_course):
    author_course.is_active = False
    author_course.save()
    response = client.get(reverse("author_courses:author_course_detail", args=[author_course.slug]))
    assert response.status_code == 404
