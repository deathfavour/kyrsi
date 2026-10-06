import json
from functools import lru_cache
from pathlib import Path

from django.shortcuts import render

from .services import CURRENT, FUTURE, SERVICES

PHOTO_CREDITS_FILE = Path(__file__).resolve().parent / "photo_credits.json"


def our_services(request):
    return render(
        request,
        "pages/our_services.html",
        {
            "current_services": [s for s in SERVICES if s["status"] == CURRENT],
            "future_services": [s for s in SERVICES if s["status"] == FUTURE],
            "group_services": [s for s in SERVICES if s["branch"] == "services"],
        },
    )


def about_us(request):
    return render(request, "pages/about_us.html")


def contact_us(request):
    return render(request, "pages/contact_us.html")


@lru_cache(maxsize=1)
def _photo_credits():
    with PHOTO_CREDITS_FILE.open(encoding="utf-8") as f:
        credits = json.load(f)
    return sorted(credits.items())


def photo_credits(request):
    """Attribution for every photo on the site (CC BY / CC BY-SA licences require
    it). Data: pages/photo_credits.json, keyed by path under static/img/."""
    credits = _photo_credits()
    return render(
        request,
        "pages/photo_credits.html",
        {
            "commons": [(path, c) for path, c in credits if c["source"] == "Wikimedia Commons"],
            "partner": [(path, c) for path, c in credits if c["source"] != "Wikimedia Commons"],
        },
    )
