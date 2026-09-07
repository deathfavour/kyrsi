from django.urls import path

from . import views

app_name = "refunds"

urlpatterns = [
    path("refunds/request/", views.request_refund, name="request_refund"),
]
