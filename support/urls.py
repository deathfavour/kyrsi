from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("support/ask/", views.ask_question, name="ask_question"),
]
