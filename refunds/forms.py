from django import forms
from django.utils.translation import gettext_lazy as _

from payments.models import Payment

from .models import RefundRequest

_INPUT_CLASSES = (
    "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-blue-950/20 focus:border-blue-950"
)


class RefundRequestForm(forms.Form):
    """Кандидат не имеет аккаунта (см. CLAUDE.md "Без аккаунта у кандидата") —
    свой Payment находит по invoice_number + email, введённым вручную,
    не выбором из списка."""

    invoice_number = forms.CharField(label=_("Invoice Number"), widget=forms.TextInput(
        attrs={"class": _INPUT_CLASSES, "placeholder": "INV-20260101-000001"}
    ))
    email = forms.EmailField(label=_("Email used at checkout"), widget=forms.EmailInput(
        attrs={"class": _INPUT_CLASSES}
    ))
    reason = forms.CharField(label=_("Reason for refund"), widget=forms.Textarea(
        attrs={"class": _INPUT_CLASSES, "rows": 4}
    ))

    def clean(self):
        cleaned_data = super().clean()
        invoice_number = cleaned_data.get("invoice_number")
        email = cleaned_data.get("email")
        if not invoice_number or not email:
            return cleaned_data

        try:
            payment = Payment.objects.select_related("application").get(
                invoice_number=invoice_number, application__email__iexact=email
            )
        except Payment.DoesNotExist:
            raise forms.ValidationError(
                _("We couldn't find a payment matching that invoice number and email.")
            )

        if payment.status != Payment.Status.PAID:
            raise forms.ValidationError(
                _("Refunds can only be requested for completed payments.")
            )

        cleaned_data["payment"] = payment
        return cleaned_data

    def save(self):
        return RefundRequest.objects.create(
            payment=self.cleaned_data["payment"],
            reason=self.cleaned_data["reason"],
        )
