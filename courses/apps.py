from django.apps import AppConfig


class CoursesConfig(AppConfig):
    name = 'courses'

    def ready(self):
        from auditlog.registry import auditlog

        from .models import Course, TrainingCenter

        auditlog.register(Course)
        auditlog.register(TrainingCenter)
