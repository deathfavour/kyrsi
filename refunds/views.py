from django.shortcuts import render

from notifications.services import notify_refund_requested

from .forms import RefundRequestForm


def request_refund(request):
    if request.method == "POST":
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            refund_request = form.save()
            notify_refund_requested(refund_request)
            return render(request, "refunds/request_success.html", {
                "refund_request": refund_request,
            })
    else:
        form = RefundRequestForm()

    return render(request, "refunds/request_form.html", {"form": form})
