from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Course, TrainingCenter


@admin.register(TrainingCenter)
class TrainingCenterAdmin(admin.ModelAdmin):
    list_display = ("name", "bank_country", "currency", "is_active")
    list_filter = ("is_active", "bank_country")
    search_fields = ("name", "contact_email")


@admin.register(Course)
class CourseAdmin(TranslationAdmin):
    list_display = (
        "title",
        "training_center",
        "category",
        "topic",
        "level",
        "training_center_price_usd",
        "price_usd",
        "commission_percent",
        "is_active",
    )
    list_filter = ("is_active", "training_center", "category", "topic", "level")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
