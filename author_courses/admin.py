from django.contrib import admin

from .models import AuthorCourse, CareerPathProgram


@admin.register(AuthorCourse)
class AuthorCourseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "level", "price_usd", "order", "is_active")
    list_filter = ("is_active", "category", "level")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(CareerPathProgram)
class CareerPathProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price_usd", "order", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
