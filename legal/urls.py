from django.urls import path

from . import views

app_name = "legal"

urlpatterns = [
    path("terms/", views.terms, name="terms"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("refund-policy/", views.refund_policy, name="refund_policy"),
]
