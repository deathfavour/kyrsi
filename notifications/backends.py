import logging

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


class NotificationBackend:
    """Общий интерфейс канала уведомлений (email / Telegram / WhatsApp).

    Один и тот же вызывающий код (см. notifications/services.py) работает
    с любым каналом через send_message()/send_email() — конкретная реализация
    (или её отсутствие, как для WhatsApp) скрыта за этим интерфейсом."""

    def send_message(self, text):
        raise NotImplementedError

    def send_email(self, subject, text_body, to, html_body=None, attachments=None):
        raise NotImplementedError


class EmailBackend(NotificationBackend):
    def send_message(self, text):
        raise NotImplementedError("EmailBackend requires a subject/recipient — use send_email().")

    def send_email(self, subject, text_body, to, html_body=None, attachments=None):
        email = EmailMultiAlternatives(subject=subject, body=text_body, to=[to])
        if html_body is not None:
            email.attach_alternative(html_body, "text/html")
        for name, content in (attachments or []):
            email.attach(name, content, "application/pdf")
        email.send(fail_silently=False)


class TelegramBackend(NotificationBackend):
    """Минимальный исходящий вызов Telegram Bot API (POST sendMessage).

    Не интерактивный бот — команды и FAQ-матрица не входят в текущий объём
    (см. CLAUDE.md "Открыто"), это только outbound-уведомления партнёру."""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def send_message(self, text):
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            logger.info("Telegram is not configured, skipping notification: %s", text)
            return

        url = self.API_URL.format(token=settings.TELEGRAM_BOT_TOKEN)
        response = requests.post(
            url, data={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text}, timeout=10
        )
        if not response.ok:
            logger.warning("Telegram notification failed: %s", response.text)

    def send_email(self, subject, text_body, to, html_body=None, attachments=None):
        raise NotImplementedError("TelegramBackend does not support send_email().")


class WhatsAppBackend(NotificationBackend):
    """Заглушка: WhatsApp Business API требует верификации бизнеса в Meta,
    не реализовано (см. CLAUDE.md "Стек" и "Открыто"). Интерфейс уже
    соответствует NotificationBackend, чтобы включение свелось к реализации
    send_message() без изменений в вызывающем коде."""

    def send_message(self, text):
        logger.info("WhatsApp backend is not implemented yet, skipping: %s", text)

    def send_email(self, subject, text_body, to, html_body=None, attachments=None):
        raise NotImplementedError("WhatsAppBackend does not support send_email().")
