from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    name = 'applications'

    def ready(self):
        from auditlog.registry import auditlog

        from .models import Application

        auditlog.register(Application)
