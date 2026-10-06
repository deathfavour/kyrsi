from django.contrib import admin

from .models import AuthorCourse, CareerPathProgram


@admin.register(AuthorCourse)
class AuthorCourseAdmin(admin.ModelAdmin):
    list_display = ("title", "author_name", "category", "level", "price_usd", "order", "is_active")
    list_filter = ("is_active", "category", "level")
    search_fields = ("title", "slug", "author_name")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "description", "is_active", "order")}),
        ("Course facts", {"fields": ("category", "level", "duration", "price_usd")}),
        (
            "Course page",
            {
                "fields": (
                    "author_name",
                    "objective",
                    "target_audience",
                    "learning_outcomes",
                    "certificate",
                )
            },
        ),
    )


@admin.register(CareerPathProgram)
class CareerPathProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price_usd", "order", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
