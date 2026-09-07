import hashlib
import re
from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings

register = template.Library()

# Matches the section headers used when the fixture description was assembled
# (see courses/fixtures/courses.json — "What You Will Learn:", "Why This Course
# Matters:", "Career Value:"). Free text without these headers still renders —
# it just stays entirely in "overview".
_SECTION_RE = re.compile(
    r"\n\n(What You Will Learn|Why This Course Matters|Career Value):\n", re.IGNORECASE
)


# course-preview.jpg always shows all three cards (Why Take/You Will Learn/Career
# Value), but 22 and 26 of 53 courses respectively have no matching section in
# Course_Description.docx. Generic fallback text keeps the layout consistent
# instead of hiding a card — same approach as recommended_for's category fallback.
# Not customer-confirmed per-course copy, just a display-layer placeholder.
_FALLBACK_WHY_MATTERS = (
    "This training addresses a real operational need onboard, helping crews "
    "reduce risk and stay aligned with international maritime standards."
)
_FALLBACK_CAREER_VALUE = (
    "Completing this course strengthens your professional competence and "
    "supports career advancement in the maritime industry."
)


@register.filter
def parse_course_description(description):
    """Splits Course.description into overview/learn_points/why_matters/career_value
    for the course-preview.jpg layout (three separate cards). No structured fields
    exist on the model for this — the text was assembled with these headers as
    section markers when the fixture was built, so we split back on them here
    rather than migrating the schema for a display-only concern."""
    if not description:
        return {
            "overview": "",
            "learn_points": [],
            "why_matters": _FALLBACK_WHY_MATTERS,
            "career_value": _FALLBACK_CAREER_VALUE,
        }

    parts = _SECTION_RE.split(description)
    result = {
        "overview": parts[0].strip(),
        "learn_points": [],
        "why_matters": "",
        "career_value": "",
    }

    for i in range(1, len(parts), 2):
        heading = parts[i].strip().lower()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if heading == "what you will learn":
            result["learn_points"] = [
                line.lstrip("-").strip() for line in body.splitlines() if line.strip()
            ]
        elif heading == "why this course matters":
            result["why_matters"] = body
        elif heading == "career value":
            result["career_value"] = body

    result["why_matters"] = result["why_matters"] or _FALLBACK_WHY_MATTERS
    result["career_value"] = result["career_value"] or _FALLBACK_CAREER_VALUE

    return result


_prefix = "Recommended for:"

# 26 of 53 courses have no "Recommended for" section in Course_Description.docx
# (empty Course.requirements) — course-preview.jpg always shows this card, so a
# generic fallback by category keeps the layout consistent instead of hiding the
# block. Not customer-confirmed per-course, same caveat as level/category/topic
# (see CLAUDE.md "Открыто").
_FALLBACK_RECOMMENDED_FOR = {
    "navigators": ["Deck Officers", "Navigating Officers", "Masters", "Cadets"],
    "engineers": ["Engineering Officers", "Marine Engineers", "ETOs", "Cadets"],
}


@register.filter
def recommended_for(course):
    """Course.requirements is stored as "Recommended for: A, B, C" (see fixture).
    Splits it into a list for the "Who is this course for?" card, falling back to
    a generic by-category list when the course has no requirements text."""
    requirements = course.requirements
    if requirements and requirements.strip().lower().startswith(_prefix.lower()):
        return [item.strip() for item in requirements.split(":", 1)[1].split(",") if item.strip()]
    return _FALLBACK_RECOMMENDED_FOR.get(course.category, [])


@register.filter
def first_sentence(text):
    """Short hook line under the course title (see course-preview.jpg — e.g.
    "Master Safe Propulsion and Steering Operations"). No dedicated field for
    this on Course — reuses the first sentence of the overview paragraph."""
    if not text:
        return ""
    match = re.search(r"^(.*?[.!?])(\s|$)", text.strip())
    return match.group(1) if match else text.strip()


# One unique photo per Course.slug in static/img/catalog/ — not shared by topic.
_FALLBACK_CATALOG = "img/course-generic-maritime.jpg"


@lru_cache(maxsize=1)
def _catalog_slugs():
    folder = Path(settings.BASE_DIR) / "static" / "img" / "catalog"
    if not folder.exists():
        return ()
    return tuple(sorted(p.stem for p in folder.glob("*.jpg")))


def _catalog_image(slug):
    if slug and slug in _catalog_slugs():
        return f"img/catalog/{slug}.jpg"
    return _FALLBACK_CATALOG


@register.filter
def course_thumbnail(course):
    return _catalog_image(getattr(course, "slug", None))


@register.filter
def course_hero_image(course):
    return _catalog_image(getattr(course, "slug", None))


@register.filter
def course_gallery(course):
    """Own unique photo plus three other catalog photos, offset by slug
    so neighbouring courses do not share the same strip."""
    own = _catalog_image(getattr(course, "slug", None))
    slugs = [s for s in _catalog_slugs() if s != getattr(course, "slug", None)]
    if len(slugs) < 3:
        return [own, own, own, own]
    seed = int(hashlib.md5(course.slug.encode()).hexdigest(), 16)
    start = seed % len(slugs)
    others = [f"img/catalog/{slugs[(start + i * 11) % len(slugs)]}.jpg" for i in range(3)]
    return [own, *others]


@register.filter
def instructor_portrait(course):
    person = "engineer" if course.category == "engineers" else "navigator"
    return f"img/portrait-{person}.jpg"
