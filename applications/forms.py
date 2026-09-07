from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    MAX_DOCUMENT_SIZE_BYTES,
    Application,
    ApplicationDocument,
)

_INPUT_CLASSES = (
    "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-blue-950/20 focus:border-blue-950"
)
_FILE_INPUT_CLASSES = "w-full text-sm text-slate-600"


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            "full_name",
            "date_of_birth",
            "citizenship",
            "position",
            "company",
            "phone",
            "email",
            "comments",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": _INPUT_CLASSES}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": _INPUT_CLASSES}),
            "citizenship": forms.TextInput(attrs={"class": _INPUT_CLASSES}),
            "position": forms.TextInput(attrs={"class": _INPUT_CLASSES}),
            "company": forms.TextInput(attrs={"class": _INPUT_CLASSES}),
            "phone": forms.TextInput(attrs={"class": _INPUT_CLASSES}),
            "email": forms.EmailInput(attrs={"class": _INPUT_CLASSES}),
            "comments": forms.Textarea(attrs={"rows": 3, "class": _INPUT_CLASSES}),
        }


class ApplicationDocumentsForm(forms.Form):
    """Загрузка документов на шаге 2 (см. ref-design/payment_tab1.png).

    Seaman's Book и Certificate of Competency обязательны, остальное — опционально.
    Одна форма с явным полем на слот, а не formset: набор слотов фиксирован макетом.
    """

    seamans_book = forms.FileField(
        required=True,
        label=_("Seaman's Book"),
        widget=forms.ClearableFileInput(attrs={"class": _FILE_INPUT_CLASSES}),
    )
    certificate_of_competency = forms.FileField(
        required=True,
        label=_("Certificate of Competency"),
        widget=forms.ClearableFileInput(attrs={"class": _FILE_INPUT_CLASSES}),
    )
    medical_certificate = forms.FileField(
        required=False,
        label=_("Medical Certificate"),
        widget=forms.ClearableFileInput(attrs={"class": _FILE_INPUT_CLASSES}),
    )
    passport = forms.FileField(
        required=False,
        label=_("Passport (ID page)"),
        widget=forms.ClearableFileInput(attrs={"class": _FILE_INPUT_CLASSES}),
    )
    other = forms.FileField(
        required=False,
        label=_("Other document"),
        widget=forms.ClearableFileInput(attrs={"class": _FILE_INPUT_CLASSES}),
    )

    FIELD_TO_DOCUMENT_TYPE = {
        "seamans_book": ApplicationDocument.SEAMANS_BOOK,
        "certificate_of_competency": ApplicationDocument.CERTIFICATE_OF_COMPETENCY,
        "medical_certificate": ApplicationDocument.MEDICAL_CERTIFICATE,
        "passport": ApplicationDocument.PASSPORT,
        "other": ApplicationDocument.OTHER,
    }

    def clean(self):
        cleaned_data = super().clean()
        for field_name in self.FIELD_TO_DOCUMENT_TYPE:
            uploaded_file = cleaned_data.get(field_name)
            if uploaded_file is None:
                continue
            extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
            if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
                self.add_error(
                    field_name,
                    _("Unsupported file type. Allowed: PDF, JPG, PNG."),
                )
            elif uploaded_file.size > MAX_DOCUMENT_SIZE_BYTES:
                self.add_error(field_name, _("File must be 5MB or smaller."))
        return cleaned_data

    def save(self, application):
        documents = []
        for field_name, document_type in self.FIELD_TO_DOCUMENT_TYPE.items():
            uploaded_file = self.cleaned_data.get(field_name)
            if uploaded_file is None:
                continue
            documents.append(
                ApplicationDocument(
                    application=application,
                    document_type=document_type,
                    file=uploaded_file,
                )
            )
        ApplicationDocument.objects.bulk_create(documents)
        return documents


class TermsConfirmationForm(forms.Form):
    """Шаг 3 флоу покупки — четыре обязательных чекбокса (см. CLAUDE.md)."""

    agree_purchase_terms = forms.BooleanField(
        required=True, label=_("I agree to the purchase terms")
    )
    agree_refund_policy = forms.BooleanField(
        required=True, label=_("I agree to the refund policy")
    )
    agree_gdpr = forms.BooleanField(
        required=True, label=_("I agree to the processing of my personal data (GDPR)")
    )
    agree_representative = forms.BooleanField(
        required=True,
        label=_("I confirm the company is the official representative of the training center"),
    )
