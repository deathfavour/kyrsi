from author_courses.models import AuthorCourse, CareerPathProgram
from author_courses.templatetags.author_course_extras import (
    author_course_thumbnail,
    career_path_thumbnail,
)


def test_author_course_thumbnail_is_unique_per_slug():
    brm = AuthorCourse(slug="bridge-resource-management", title="BRM", price_usd=75)
    ice = AuthorCourse(slug="ice-navigation-essentials", title="Ice", price_usd=85)
    assert author_course_thumbnail(brm) == "img/author/bridge-resource-management.jpg"
    assert author_course_thumbnail(ice) == "img/author/ice-navigation-essentials.jpg"
    assert author_course_thumbnail(brm) != author_course_thumbnail(ice)


def test_career_path_thumbnail_is_unique_per_slug():
    cadet = CareerPathProgram(slug="deck-cadet-first-step", title="Cadet", price_usd=120)
    tanker = CareerPathProgram(
        slug="oil-chemical-gas-tanker-specialist-program", title="Tanker", price_usd=140
    )
    assert career_path_thumbnail(cadet) == "img/author/deck-cadet-first-step.jpg"
    assert career_path_thumbnail(tanker) != career_path_thumbnail(cadet)
