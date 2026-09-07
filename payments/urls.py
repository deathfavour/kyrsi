from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("apply/<slug:course_slug>/pay/<int:pk>/", views.initiate, name="initiate"),
    path("apply/<slug:course_slug>/pay/<int:pk>/success/", views.success, name="success"),
    path("webhook/fondy/", views.fondy_webhook, name="fondy_webhook"),
]
