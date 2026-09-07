from django.shortcuts import render

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
