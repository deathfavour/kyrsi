import json

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from applications.models import Application
from courses.models import Course

from . import fondy
from .models import Payment
from .tasks import process_paid_payment

PAYMENT_NOTIFICATION_DELAY_SECONDS = 15 * 60


@require_POST
def initiate(request, course_slug, pk):
    """Шаг 4 флоу покупки — редирект на Fondy Checkout."""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    application = get_object_or_404(
        Application, pk=pk, course=course, agreed_terms_at__isnull=False
    )
    payment, created = Payment.objects.get_or_init_for_application(application)

    if payment.status == Payment.Status.PAID:
        return redirect("payments:success", course_slug=course.slug, pk=application.pk)

    if not created:
        # Старый order_id мог уже быть отправлен в Fondy и не годится для новой попытки.
        payment.refresh_fondy_order_id()

    server_callback_url = request.build_absolute_uri(reverse("payments:fondy_webhook"))
    response_url = request.build_absolute_uri(
        reverse("payments:success", args=[course.slug, application.pk])
    )

    checkout_url = fondy.create_checkout_url(
        payment, server_callback_url=server_callback_url, response_url=response_url
    )
    return redirect(checkout_url)


def success(request, course_slug, pk):
    """response_url — куда Fondy возвращает браузер кандидата после оплаты."""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    application = get_object_or_404(Application, pk=pk, course=course)
    payment = get_object_or_404(Payment, application=application)
    return render(
        request,
        "payments/success.html",
        {"course": course, "application": application, "payment": payment},
    )


@csrf_exempt
@require_POST
def fondy_webhook(request):
    """server_callback_url — основной канал уведомлений от Fondy (см. CLAUDE.md)."""
    data = request.POST.dict()
    if not data and request.body:
        try:
            data = json.loads(request.body)
        except ValueError:
            data = {}

    if not fondy.verify_signature(data):
        return HttpResponseForbidden("invalid signature")

    payment = Payment.objects.filter(fondy_order_id=data.get("order_id")).first()
    if payment is None:
        return HttpResponse(status=404)

    order_status = data.get("order_status")
    if order_status == "approved":
        if payment.status != Payment.Status.PAID:
            payment.status = Payment.Status.PAID
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at"])
            process_paid_payment.apply_async(
                args=[payment.pk], countdown=PAYMENT_NOTIFICATION_DELAY_SECONDS
            )
    elif order_status in ("declined", "expired"):
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])

    return HttpResponse("OK")
