from unittest.mock import MagicMock, patch

import pytest
from django.core import mail

from notifications.backends import EmailBackend, TelegramBackend, WhatsAppBackend


def test_email_backend_sends_html_and_text_alternative():
    backend = EmailBackend()
    backend.send_email(
        subject="Test subject",
        text_body="plain text body",
        to="candidate@example.com",
        html_body="<p>html body</p>",
    )

    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ["candidate@example.com"]
    assert sent.body == "plain text body"
    assert sent.alternatives == [("<p>html body</p>", "text/html")]


def test_email_backend_attaches_files():
    backend = EmailBackend()
    backend.send_email(
        subject="Test subject",
        text_body="body",
        to="candidate@example.com",
        attachments=[("invoice.pdf", b"%PDF-fake%")],
    )

    sent = mail.outbox[0]
    assert sent.attachments == [("invoice.pdf", b"%PDF-fake%", "application/pdf")]


def test_email_backend_send_message_not_supported():
    backend = EmailBackend()
    with pytest.raises(NotImplementedError):
        backend.send_message("hello")


def test_telegram_backend_skips_when_not_configured(settings):
    settings.TELEGRAM_BOT_TOKEN = ""
    settings.TELEGRAM_CHAT_ID = ""
    backend = TelegramBackend()
    with patch("notifications.backends.requests.post") as mock_post:
        backend.send_message("hello")
    mock_post.assert_not_called()


def test_telegram_backend_posts_when_configured(settings):
    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.TELEGRAM_CHAT_ID = "12345"
    backend = TelegramBackend()

    mock_response = MagicMock(ok=True)
    with patch("notifications.backends.requests.post", return_value=mock_response) as mock_post:
        backend.send_message("hello")

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.telegram.org/bottest-token/sendMessage"
    assert kwargs["data"] == {"chat_id": "12345", "text": "hello"}


def test_telegram_backend_send_email_not_supported():
    backend = TelegramBackend()
    with pytest.raises(NotImplementedError):
        backend.send_email("subject", "body", "to@example.com")


def test_whatsapp_backend_send_message_is_a_no_op():
    backend = WhatsAppBackend()
    backend.send_message("hello")  # should not raise


def test_whatsapp_backend_send_email_not_supported():
    backend = WhatsAppBackend()
    with pytest.raises(NotImplementedError):
        backend.send_email("subject", "body", "to@example.com")
