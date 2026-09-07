from modeltranslation.translator import TranslationOptions, register

from .models import Course


@register(Course)
class CourseTranslationOptions(TranslationOptions):
    fields = ("title", "description", "requirements", "instructor_bio")
