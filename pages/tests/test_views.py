import re

import pytest
from django.urls import reverse

from pages.site_info import SITE_INFO


def test_our_services_separates_current_and_future_services(client, db):
    response = client.get(reverse("pages:our_services"))
    content = response.content.decode()
    assert response.status_code == 200
    current = [str(s["title"]) for s in response.context["current_services"]]
    future = [str(s["title"]) for s in response.context["future_services"]]
    assert current == [
        "Maritime Training",
        "Recruitment Services",
        "HR Department Support",
        "Payroll Services",
        "Introduction & Partnership",
    ]
    assert "Vessel Management" in future and "Ship Brokerage" in future
    assert "FUTURE MARITIME SERVICES" in content
    assert "Coming Soon" in content


def test_contact_page_uses_single_source_of_contacts(client, db):
    content = client.get(reverse("pages:contact_us")).content.decode()
    assert SITE_INFO["head_office"] in content
    assert "Varna, Bulgaria" in content
    assert "Sofia" not in content
    assert "+359 89 123 45 67" not in content
    for social in SITE_INFO["socials"]:
        assert social["url"] in content


def test_about_page_separates_academy_and_training_partner(client, db):
    content = client.get(reverse("pages:about_us")).content.decode()
    assert "Education platform of Garant Marine Group" in content
    assert "Official training partner / training provider" in content
    assert SITE_INFO["partner_address"] in content
    assert "img/site/gmg-logo-white.png" in content


def test_photo_credits_lists_every_commons_image(client, db):
    response = client.get(reverse("pages:photo_credits"))
    assert response.status_code == 200
    for path, credit in response.context["commons"]:
        assert credit["license"]
        assert credit["page"].startswith("https://commons.wikimedia.org/")
        assert f"img/{path}" in response.content.decode()


PUBLIC_PAGES = [
    "courses:home",
    "courses:course_list",
    "author_courses:author_course_list",
    "pages:our_services",
    "pages:about_us",
    "pages:contact_us",
    "legal:terms",
    "legal:privacy_policy",
    "legal:refund_policy",
    "refunds:request_refund",
    "support:ask_question",
]

# Customer edits 2026-10-05: one refund policy everywhere (п.18), no unconfirmed
# "approved by" claims (п.7, 15, 23), no emoji/keyboard symbols as icons (п.4),
# no payment provider named while it is not chosen.
FORBIDDEN = [
    "7 days",
    "14-Day Money Back",
    "Approved ISO",
    "Approved Maritime Classification Society",
    "ISO 9001 principles",
    "Fondy",
    "Powered by Meridian",
]
EMOJI_ENTITY = re.compile(r"&#(1[0-9]{4,5}|9[0-9]{3}|8[5-9][0-9]{2});")


@pytest.mark.parametrize("url_name", PUBLIC_PAGES)
def test_public_pages_have_consistent_wording(client, db, url_name):
    content = client.get(reverse(url_name)).content.decode()
    for phrase in FORBIDDEN:
        assert phrase not in content, f"{phrase!r} on {url_name}"
    assert not EMOJI_ENTITY.search(content), f"emoji entity on {url_name}"
    assert SITE_INFO["head_office"] in content
    assert "In partnership with Meridian Maritime Training Center" in content
