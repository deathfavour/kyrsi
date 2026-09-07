import pytest

from payments.pdf import html_to_pdf


def test_html_to_pdf_renders_real_pdf_bytes():
    try:
        result = html_to_pdf("<h1>Test</h1>")
    except OSError as exc:
        pytest.skip(f"WeasyPrint native libraries are not available in this environment: {exc}")
    assert result.startswith(b"%PDF")
