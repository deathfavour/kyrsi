from django.shortcuts import get_object_or_404, render

from .models import Course


def home(request):
    return render(request, "courses/home.html")


def course_list(request):
    courses = Course.objects.filter(is_active=True).select_related("training_center")
    hero_courses = _hero_courses(courses)
    return render(
        request,
        "courses/course_list.html",
        {
            "courses": courses,
            "hero_courses": hero_courses,
            "topics": Course.Topic.choices,
        },
    )


def _hero_courses(courses):
    """4 real courses spanning different topics for the online_courses.jpg-style
    hero carousel — not invented promo scenarios, an actual cross-section of the
    catalog (see CLAUDE.md "Каталог курсов")."""
    seen_topics = set()
    picks = []
    for course in courses.order_by("title"):
        if course.topic in seen_topics:
            continue
        seen_topics.add(course.topic)
        picks.append(course)
        if len(picks) == 4:
            break
    return picks


def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related("training_center"), slug=slug, is_active=True
    )
    return render(request, "courses/course_detail.html", {"course": course})
