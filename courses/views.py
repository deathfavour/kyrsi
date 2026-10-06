from django.shortcuts import get_object_or_404, render

from .models import Course

# Short area descriptions for the home "Our Maritime Learning Areas" block
# (customer edits 2026-10-05, п.5: icon + short description + example courses +
# link to all courses of the area).
LEARNING_AREA_INFO = {
    Course.LearningArea.MARINE_ENGINEERING: {
        "icon": "cog",
        "description": (
            "Main and auxiliary machinery, hydraulics, compressed air and dual-fuel systems."
        ),
    },
    Course.LearningArea.NAVIGATION: {
        "icon": "compass",
        "description": (
            "ECDIS, collision regulations, ship handling and bridge resource management."
        ),
    },
    Course.LearningArea.TANKER_OPERATIONS: {
        "icon": "droplets",
        "description": "Liquid cargo and ballast operations on oil, chemical and LPG tankers.",
    },
    Course.LearningArea.SAFETY_COMPLIANCE: {
        "icon": "shield-check",
        "description": "MARPOL, ISM, inspections, risk assessment and emergency response.",
    },
    Course.LearningArea.LEADERSHIP_HUMAN_FACTORS: {
        "icon": "users",
        "description": "Leadership, communication, wellbeing and human performance onboard.",
    },
}

EXAMPLES_PER_AREA = 4


def _active_courses():
    return Course.objects.filter(is_active=True).select_related("training_center")


def catalog_stats(courses):
    """Home-page figures computed from the live catalog (п.6: "все цифры должны
    соответствовать реальному каталогу"), not hardcoded marketing numbers.
    Hours are rounded down to the nearest 50 and shown with "+" — a few courses
    still have duration "TBD" and are not counted."""
    courses = list(courses)
    total_hours = sum(c.duration_hours or 0 for c in courses)
    return {
        "courses": len(courses),
        "hours": total_hours // 50 * 50,
        "areas": len(Course.LearningArea.choices),
    }


def home(request):
    courses = list(_active_courses())
    areas = []
    for value, label in Course.LearningArea.choices:
        area_courses = [c for c in courses if c.learning_area == value]
        areas.append(
            {
                "value": value,
                "label": label,
                **LEARNING_AREA_INFO[value],
                "examples": area_courses[:EXAMPLES_PER_AREA],
                "count": len(area_courses),
            }
        )
    return render(
        request,
        "courses/home.html",
        {"areas": areas, "stats": catalog_stats(courses)},
    )


def course_list(request):
    courses = _active_courses()
    area = request.GET.get("area", "all")
    if area not in Course.LearningArea.values:
        area = "all"
    return render(
        request,
        "courses/course_list.html",
        {
            "courses": courses,
            "hero_courses": _hero_courses(courses),
            "areas": Course.LearningArea.choices,
            "initial_area": area,
            "catalog_index": [[c.category, c.learning_area, c.title.lower()] for c in courses],
        },
    )


def _hero_courses(courses):
    """4 real courses from different learning areas for the online_courses.jpg-style
    hero carousel — an actual cross-section of the catalog, not invented promos."""
    seen_areas = set()
    picks = []
    for course in courses.order_by("title"):
        if course.learning_area in seen_areas:
            continue
        seen_areas.add(course.learning_area)
        picks.append(course)
        if len(picks) == 4:
            break
    return picks


def course_detail(request, slug):
    course = get_object_or_404(_active_courses(), slug=slug)
    return render(request, "courses/course_detail.html", {"course": course})
