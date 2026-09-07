from django import forms
from django.utils.translation import gettext_lazy as _

from .models import SupportTicket

_INPUT_CLASSES = (
    "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-blue-950/20 focus:border-blue-950"
)


class SupportQuestionForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["applicant_name", "applicant_email", "applicant_phone", "message"]
        widgets = {
            "applicant_name": forms.TextInput(attrs={"class": _INPUT_CLASSES}),
            "applicant_email": forms.EmailInput(attrs={"class": _INPUT_CLASSES}),
            "applicant_phone": forms.TextInput(attrs={"class": _INPUT_CLASSES}),
            "message": forms.Textarea(attrs={"class": _INPUT_CLASSES, "rows": 4}),
        }
        labels = {
            "applicant_name": _("Full Name"),
            "applicant_email": _("Email"),
            "applicant_phone": _("Phone (optional)"),
            "message": _("How can we help you?"),
        }

    def save(self, commit=True):
        ticket = super().save(commit=False)
        ticket.ticket_type = SupportTicket.TicketType.QUESTION
        if commit:
            ticket.save()
        return ticket
