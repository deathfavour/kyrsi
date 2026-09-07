from support.models import SupportTicket


def test_support_ticket_default_status_is_open(db):
    ticket = SupportTicket.objects.create(
        ticket_type=SupportTicket.TicketType.QUESTION,
        applicant_name="Jane Seafarer",
        applicant_email="jane@example.com",
        message="How long does the course take?",
    )
    assert ticket.status == SupportTicket.Status.OPEN


def test_support_ticket_str(db):
    ticket = SupportTicket.objects.create(
        ticket_type=SupportTicket.TicketType.QUESTION,
        applicant_name="Jane Seafarer",
        applicant_email="jane@example.com",
        message="Test.",
    )
    assert "Jane Seafarer" in str(ticket)
