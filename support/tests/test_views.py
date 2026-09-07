from django.core import mail
from django.urls import reverse

from support.models import SupportTicket


def test_get_ask_question_renders_form(client, db):
    response = client.get(reverse("support:ask_question"))
    assert response.status_code == 200
    assert b"ASK A QUESTION" in response.content


def test_post_valid_data_creates_ticket_and_notifies(client, db, settings):
    settings.PARTNER_NOTIFICATION_EMAIL = "partner@example.com"

    response = client.post(reverse("support:ask_question"), data={
        "applicant_name": "Jane Seafarer",
        "applicant_email": "jane@example.com",
        "applicant_phone": "",
        "message": "How long does the course take?",
    })

    assert response.status_code == 200
    ticket = SupportTicket.objects.get()
    assert ticket.ticket_type == SupportTicket.TicketType.QUESTION
    assert ticket.applicant_name == "Jane Seafarer"

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["partner@example.com"]


def test_post_invalid_data_rerenders_form(client, db):
    response = client.post(reverse("support:ask_question"), data={
        "applicant_name": "",
        "applicant_email": "not-an-email",
        "message": "",
    })

    assert response.status_code == 200
    assert SupportTicket.objects.count() == 0
