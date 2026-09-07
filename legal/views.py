from django.shortcuts import render


def terms(request):
    return render(request, "legal/terms.html")


def privacy_policy(request):
    return render(request, "legal/privacy_policy.html")


def refund_policy(request):
    return render(request, "legal/refund_policy.html")
