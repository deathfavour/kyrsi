from django.contrib import admin

from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ticket_type",
        "applicant_name",
        "applicant_email",
        "status",
        "created_at",
    )
    list_filter = ("status", "ticket_type")
    search_fields = ("applicant_name", "applicant_email", "message")
    date_hierarchy = "created_at"
