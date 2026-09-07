from pathlib import Path

from django import template
from django.conf import settings

register = template.Library()

_FALLBACK = "img/course-generic-maritime.jpg"


def _unique_image(folder, slug):
    if not slug:
        return _FALLBACK
    rel = f"img/{folder}/{slug}.jpg"
    full = Path(settings.BASE_DIR) / "static" / rel
    return rel if full.exists() else _FALLBACK


@register.filter
def author_course_thumbnail(course):
    return _unique_image("author", getattr(course, "slug", None))


@register.filter
def career_path_thumbnail(program):
    return _unique_image("author", getattr(program, "slug", None))
