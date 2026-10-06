import re

import pytest
from django.core.management import call_command

from applications.models import Application


@pytest.fixture
def catalog(db):
    call_command("loaddata", "training_centers.json")
    call_command("loaddata", "courses.json")


def test_static_preview_exports_site_under_base_path(catalog, tmp_path):
    call_command("build_static_preview", out=str(tmp_path), base_path="/kyrsi/")

    home = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'href="/kyrsi/courses/"' in home
    assert 'src="/kyrsi/static/img/' in home
    assert not re.search(r'\s(?:href|src|action)="/(?!kyrsi/|/)', home)
    assert "htmx.org" not in home
    assert (tmp_path / "courses" / "man-me-b-c" / "index.html").exists()
    assert (tmp_path / "static" / "img" / "catalog" / "man-me-b-c.jpg").exists()

    apply_form = (tmp_path / "apply" / "man-me-b-c" / "index.html").read_text(encoding="utf-8")
    assert 'data-preview-next="/kyrsi/apply/man-me-b-c/confirm/"' in apply_form
    assert " hx-post=" not in apply_form
    success = (tmp_path / "apply" / "man-me-b-c" / "success" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "SUCCESSFUL TRANSACTION" in success

    # Checkout pages are rendered from throwaway objects inside a rolled-back transaction.
    assert Application.objects.count() == 0
