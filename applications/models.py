from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from courses.models import Course

ALLOWED_DOCUMENT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]
MAX_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024  # 5MB, см. ref-design/payment_tab1.png


def application_document_upload_to(instance, filename):
    return f"application_documents/{instance.application_id}/{filename}"


def validate_document_size(file):
    if file.size > MAX_DOCUMENT_SIZE_BYTES:
        raise ValidationError("File must be 5MB or smaller.")


class Application(models.Model):
    """Анкета кандидата. Без аккаунта — анонимная форма по email/телефону (см. CLAUDE.md)."""

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="applications")

    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    citizenship = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    comments = models.TextField(blank=True, null=True)

    # Таймстамп согласия со всеми четырьмя условиями шага 3 — доказательство для GDPR.
    # Проставляется целиком после подтверждения, не при создании анкеты.
    agreed_terms_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.course.title}"


class ApplicationDocument(models.Model):
    """Документ, приложенный к анкете кандидата (см. ref-design/payment_tab1.png)."""

    SEAMANS_BOOK = "seamans_book"
    CERTIFICATE_OF_COMPETENCY = "certificate_of_competency"
    MEDICAL_CERTIFICATE = "medical_certificate"
    PASSPORT = "passport"
    OTHER = "other"

    DOCUMENT_TYPE_CHOICES = [
        (SEAMANS_BOOK, "Seaman's Book"),
        (CERTIFICATE_OF_COMPETENCY, "Certificate of Competency"),
        (MEDICAL_CERTIFICATE, "Medical Certificate"),
        (PASSPORT, "Passport (ID page)"),
        (OTHER, "Other document"),
    ]

    # Обязательны в анкете (см. CLAUDE.md); остальные типы — опциональны.
    REQUIRED_DOCUMENT_TYPES = [SEAMANS_BOOK, CERTIFICATE_OF_COMPETENCY]

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=32, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(
        upload_to=application_document_upload_to,
        validators=[
            FileExtensionValidator(ALLOWED_DOCUMENT_EXTENSIONS),
            validate_document_size,
        ],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.application.full_name}"
