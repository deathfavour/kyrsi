from django.apps import AppConfig


class SupportConfig(AppConfig):
    name = 'support'

    def ready(self):
        from auditlog.registry import auditlog

        from .models import SupportTicket

        auditlog.register(SupportTicket)
