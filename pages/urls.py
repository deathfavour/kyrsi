from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("our-services/", views.our_services, name="our_services"),
    path("about-us/", views.about_us, name="about_us"),
    path("contact-us/", views.contact_us, name="contact_us"),
    path("photo-credits/", views.photo_credits, name="photo_credits"),
]
