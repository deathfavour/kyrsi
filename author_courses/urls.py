from django.urls import path

from . import views

app_name = "author_courses"

urlpatterns = [
    path("author-courses/", views.author_course_list, name="author_course_list"),
]
