import pytest
from django.core.management import call_command

from author_courses.models import AuthorCourse, CareerPathProgram


@pytest.mark.django_db
def test_author_courses_fixture_loads_and_matches_expected_counts():
    call_command("loaddata", "author_courses.json")

    assert AuthorCourse.objects.count() == 12
    assert AuthorCourse.objects.filter(category="navigators").count() == 6
    assert AuthorCourse.objects.filter(category="engineers").count() == 6

    assert CareerPathProgram.objects.count() == 8
    assert CareerPathProgram.objects.filter(category="navigators").count() == 4
    assert CareerPathProgram.objects.filter(category="engineers").count() == 4

    brm = AuthorCourse.objects.get(slug="bridge-resource-management")
    assert brm.price_usd == 75
    assert brm.category == "navigators"
