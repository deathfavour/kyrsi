from django.shortcuts import render


def our_services(request):
    return render(request, "pages/our_services.html")


def about_us(request):
    return render(request, "pages/about_us.html")


def contact_us(request):
    return render(request, "pages/contact_us.html")
