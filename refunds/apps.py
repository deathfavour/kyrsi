from django.apps import AppConfig


class RefundsConfig(AppConfig):
    name = 'refunds'

    def ready(self):
        from auditlog.registry import auditlog

        from .models import RefundRequest

        auditlog.register(RefundRequest)
