from django.shortcuts import get_object_or_404, render

from .models import AuthorCourse, CareerPathProgram


def author_course_list(request):
    author_courses = AuthorCourse.objects.filter(is_active=True)
    career_paths = CareerPathProgram.objects.filter(is_active=True)
    return render(
        request,
        "author_courses/author_course_list.html",
        {
            "author_courses": author_courses,
            "career_paths": career_paths,
        },
    )


def author_course_detail(request, slug):
    author_course = get_object_or_404(AuthorCourse, slug=slug, is_active=True)
    return render(
        request,
        "author_courses/author_course_detail.html",
        {"author_course": author_course},
    )
