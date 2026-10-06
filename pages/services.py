"""Структура услуг Garant Marine Group для /our-services/ (правки заказчика
2026-10-05, п.11–12). Новое направление — одна запись здесь, без правки шаблона;
перевод "future" → "current" — смена status.

Будущие услуги не должны выглядеть работающими: шаблон показывает их отдельным
блоком с плашкой "Coming Soon" и без ссылок "Learn more".
"""

from django.utils.translation import gettext_lazy as _

CURRENT = "current"
FUTURE = "future"

SERVICES = [
    {
        "title": _("Maritime Training"),
        "description": _(
            "Professional online courses delivered in partnership with "
            "Meridian Maritime Training Center."
        ),
        "icon": "graduation-cap",
        "status": CURRENT,
        "branch": "academy",
    },
    {
        "title": _("Recruitment Services"),
        "description": _(
            "Selection of qualified officers and ratings for shipowners, "
            "with a focus on LNG, LPG and tanker fleets."
        ),
        "icon": "user-check",
        "status": CURRENT,
        "branch": "services",
    },
    {
        "title": _("HR Department Support"),
        "description": _("HR support for maritime companies and their crews."),
        "icon": "briefcase",
        "status": CURRENT,
        "branch": "services",
    },
    {
        "title": _("Payroll Services"),
        "description": _("Safe, efficient and transparent crew salary management."),
        "icon": "wallet",
        "status": CURRENT,
        "branch": "services",
    },
    {
        "title": _("Introduction & Partnership"),
        "description": _("Connecting the right people with the right opportunities."),
        "icon": "handshake",
        "status": CURRENT,
        "branch": "services",
    },
    {
        "title": _("Vessel Management"),
        "description": _("Technical and operational management of vessels."),
        "icon": "ship",
        "status": FUTURE,
        "branch": "services",
    },
    {
        "title": _("Vessel Logistics"),
        "description": _("Logistics support for vessels and crews."),
        "icon": "truck",
        "status": FUTURE,
        "branch": "services",
    },
    {
        "title": _("Ship Brokerage"),
        "description": _("Chartering and sale & purchase brokerage."),
        "icon": "scale",
        "status": FUTURE,
        "branch": "services",
    },
    {
        "title": _("Maritime Consulting"),
        "description": _("Technical and operational consulting."),
        "note": _("Depending on development"),
        "icon": "lightbulb",
        "status": FUTURE,
        "branch": "services",
    },
    {
        "title": _("Other Maritime Services"),
        "description": _("Further directions as the group develops."),
        "icon": "layers",
        "status": FUTURE,
        "branch": "services",
    },
]
