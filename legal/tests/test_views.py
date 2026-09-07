from django.urls import reverse


def test_terms_page_renders(client, db):
    response = client.get(reverse("legal:terms"))
    assert response.status_code == 200
    assert b"TERMS" in response.content


def test_privacy_policy_page_renders(client, db):
    response = client.get(reverse("legal:privacy_policy"))
    assert response.status_code == 200
    assert b"PRIVACY POLICY" in response.content


def test_refund_policy_page_renders(client, db):
    response = client.get(reverse("legal:refund_policy"))
    assert response.status_code == 200
    assert b"REFUND POLICY" in response.content
