from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.models import Course
from payments.models import Payment

from .forms import ApplicationDocumentsForm, ApplicationForm, TermsConfirmationForm
from .models import Application


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _render_step(request, partial_template, context, step):
    """Renders just the step partial for htmx swaps, or the full wizard page otherwise."""
    if _is_htmx(request):
        return render(request, partial_template, context)
    return render(
        request,
        "applications/wizard.html",
        {**context, "step": step, "step_template": partial_template},
    )


def apply_form(request, course_slug):
    """Step 2 — заявка кандидата."""
    course = get_object_or_404(Course, slug=course_slug, is_active=True, price_usd__isnull=False)

    if request.method == "POST":
        form = ApplicationForm(request.POST)
        documents_form = ApplicationDocumentsForm(request.POST, request.FILES)
        if form.is_valid() and documents_form.is_valid():
            application = form.save(commit=False)
            application.course = course
            application.save()
            documents_form.save(application)
            return _render_step(
                request,
                "applications/_step_confirm.html",
                {
                    "course": course,
                    "application": application,
                    "confirm_form": TermsConfirmationForm(),
                },
                step=3,
            )
        return _render_step(
            request,
            "applications/_step_form.html",
            {"course": course, "form": form, "documents_form": documents_form},
            step=2,
        )

    form = ApplicationForm()
    documents_form = ApplicationDocumentsForm()
    return _render_step(
        request,
        "applications/_step_form.html",
        {"course": course, "form": form, "documents_form": documents_form},
        step=2,
    )


def apply_confirm(request, course_slug, pk):
    """Step 3 — четыре обязательных чекбокса, без них дальше пройти нельзя."""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    application = get_object_or_404(Application, pk=pk, course=course)

    if request.method == "POST":
        confirm_form = TermsConfirmationForm(request.POST)
        if confirm_form.is_valid():
            application.agreed_terms_at = timezone.now()
            application.save(update_fields=["agreed_terms_at"])
            # PRG: htmx follows the redirect and swaps the final GET response,
            # a plain form submission gets the standard post/redirect/get benefit.
            return redirect(
                "applications:apply_payment", course_slug=course.slug, pk=application.pk
            )
        return _render_step(
            request,
            "applications/_step_confirm.html",
            {"course": course, "application": application, "confirm_form": confirm_form},
            step=3,
        )

    return _render_step(
        request,
        "applications/_step_confirm.html",
        {"course": course, "application": application, "confirm_form": TermsConfirmationForm()},
        step=3,
    )


def apply_payment(request, course_slug, pk):
    """Step 4 — снэпшот суммы (курс + комиссия) и переход к оплате через Fondy."""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    application = get_object_or_404(
        Application, pk=pk, course=course, agreed_terms_at__isnull=False
    )
    payment, _created = Payment.objects.get_or_init_for_application(application)
    return _render_step(
        request,
        "applications/_step_payment.html",
        {"course": course, "application": application, "payment": payment},
        step=4,
    )
