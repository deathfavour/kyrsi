from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("apply/<slug:course_slug>/", views.apply_form, name="apply_form"),
    path("apply/<slug:course_slug>/confirm/<int:pk>/", views.apply_confirm, name="apply_confirm"),
    path(
        "apply/<slug:course_slug>/payment/<int:pk>/",
        views.apply_payment,
        name="apply_payment",
    ),
]
