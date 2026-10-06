"""`{% icon "name" "w-5 h-5" %}` — единый icon set сайта (правки заказчика 2026-10-05, п.4:
никаких emoji/HTML-сущностей вместо иконок, один стиль на весь сайт).

SVG лежат в templates/icons/: линейные иконки Lucide (ISC, см. LICENSE-lucide.txt) и
brand-*.svg из Simple Icons (CC0) для соцсетей. Вставляются инлайном, поэтому цвет
берётся из `currentColor` (text-* классы Tailwind), размер — из переданных классов.
Подключается через TEMPLATES OPTIONS "libraries" в settings (config — не Django app).
Неизвестное имя — ValueError: опечатка в шаблоне должна падать в тестах, а не тихо
пропадать со страницы.
"""

from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

ICONS_DIR = Path(settings.BASE_DIR) / "templates" / "icons"


@lru_cache(maxsize=None)
def _load(name):
    path = ICONS_DIR / f"{name}.svg"
    if not path.is_file():
        raise ValueError(f"Unknown icon: {name!r} (no {path.name} in templates/icons/)")
    return path.read_text(encoding="utf-8").strip()


@register.simple_tag
def icon(name, css="w-5 h-5"):
    svg = _load(name)
    attrs = f'class="{escape(css)} shrink-0" aria-hidden="true" focusable="false"'
    return mark_safe(svg.replace("<svg", f"<svg {attrs}", 1))
