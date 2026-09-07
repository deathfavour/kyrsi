from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("courses.urls")),
    path("", include("applications.urls")),
    path("", include("payments.urls")),
    path("", include("pages.urls")),
    path("", include("author_courses.urls")),
    path("", include("refunds.urls")),
    path("", include("support.urls")),
    path("", include("legal.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
