from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = 'payments'

    def ready(self):
        from auditlog.registry import auditlog

        from .models import Payment

        auditlog.register(Payment)
