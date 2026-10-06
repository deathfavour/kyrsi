import pytest
from django.core.management import call_command

from courses.models import Course, TrainingCenter


@pytest.mark.django_db
def test_courses_fixture_loads_and_matches_expected_counts():
    call_command("loaddata", "training_centers.json")
    call_command("loaddata", "courses.json")

    assert TrainingCenter.objects.count() == 1
    assert TrainingCenter.objects.get().name == "Meridian Maritime Training Center"
    assert Course.objects.count() == 53
    assert Course.objects.filter(price_usd__isnull=False).count() == 50
    assert Course.objects.filter(price_usd__isnull=True).count() == 3
    assert Course.objects.filter(is_active=True).count() == 53

    man_me = Course.objects.get(slug="man-me-b-c")
    assert man_me.price_usd == 650
    assert man_me.training_center_price_usd == 500
    assert man_me.duration == "20 hours"
    assert man_me.category == "engineers"
    assert man_me.instructor_name

    unpriced = Course.objects.get(slug="passage-planning-with-ecdis")
    assert unpriced.price_usd is None
    assert unpriced.has_price is False

    assert set(Course.objects.values_list("category", flat=True)) == {
        "engineers",
        "navigators",
    }
    assert set(Course.objects.values_list("learning_area", flat=True)) == set(
        Course.LearningArea.values
    )
    assert Course.objects.get(slug="framo-system").learning_area == "tanker_operations"

    crewing = Course.objects.get(slug="operation-of-crew-manning-agency")
    assert crewing.requires_seamans_book is False
    assert crewing.requires_coc is False
    assert man_me.requires_seamans_book is True
    assert man_me.requires_coc is False

    assert set(Course.objects.values_list("level", flat=True)) == {
        "beginner",
        "intermediate",
        "advanced",
    }
