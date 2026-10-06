import pytest
from django.template import Context, Template


def _render(source):
    return Template("{% load icons %}" + source).render(Context())


def test_icon_renders_inline_svg_with_classes():
    html = _render('{% icon "anchor" "w-6 h-6 text-amber-600" %}')
    assert html.startswith("<svg ")
    assert 'class="w-6 h-6 text-amber-600 shrink-0"' in html
    assert 'aria-hidden="true"' in html
    assert 'stroke="currentColor"' in html


def test_brand_icon_uses_current_color_fill():
    assert 'fill="currentColor"' in _render('{% icon "brand-linkedin" %}')


def test_unknown_icon_fails_loudly():
    with pytest.raises(ValueError, match="Unknown icon"):
        _render('{% icon "does-not-exist" %}')


def test_inner_shapes_keep_their_size_attributes():
    # Only the root <svg> loses width/height (size comes from CSS classes);
    # stripping them from <rect> breaks icons like mail/lock/monitor.
    assert '<rect width="20" height="16"' in _render('{% icon "mail" %}')
