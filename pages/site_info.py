"""Единый источник контактов, позиционирования и публичных условий (правки
заказчика 2026-10-05, п.18–20, 28: одинаковые данные на всех страницах).

Шаблоны получают это как `SITE` через pages.context_processors.site_info — не
хардкодить телефоны/адреса/сроки возврата в шаблонах, иначе они снова разъедутся.

Статус данных:
- emails info@/support@garantunitedacademy.com, bd@garantmarinegroup.com,
  Head Office 16a Bagrationi St — подтверждены заказчиком (CLAUDE.md, раунд 2 вёрстки);
- +995 593 10 40 52 — использовался на сайте во всех местах, не перепроверен;
- European Office (Varna), +359 888 285 528, соцсети GMG — с официального сайта
  garantmarinegroup.com; полный адрес в Варне заказчик пришлёт перед релизом;
- адрес и ISO-сертификат Meridian — с meridiani.ge (контакты + LRQA Certificate of Approval);
- refund 14 дней / обработка 3 рабочих дня — подтверждено заказчиком 2026-10-06.
"""

SITE_INFO = {
    "academy_name": "Garant United Academy",
    "group_name": "Garant Marine Group",
    "partner_name": "Meridian Maritime Training Center",
    "emails": {
        "info": "info@garantunitedacademy.com",
        "support": "support@garantunitedacademy.com",
        "business": "bd@garantmarinegroup.com",
    },
    "phone": "+995 593 10 40 52",
    "europe_phone": "+359 888 285 528",
    "head_office": "16a Bagrationi St, 6000 Batumi, Georgia",
    "european_office": "Varna, Bulgaria",
    "partner_address": "4a I. Javakhishvili St, 6010 Batumi, Georgia",
    "partner_website": "https://meridiani.ge/",
    "group_website": "https://garantmarinegroup.com/",
    "office_hours": "Mon – Fri, 09:00 – 18:00 (GMT+4)",
    "training_center_hours": "Mon – Fri, 10:00 – 18:00 (GMT+4)",
    # Только реальные официальные страницы (п.21). У GUA своих страниц пока нет —
    # ведём на официальные каналы Garant Marine Group с garantmarinegroup.com.
    "socials": [
        {
            "name": "LinkedIn",
            "icon": "brand-linkedin",
            "url": "https://www.linkedin.com/in/garant-marine-group-5961413b5",
        },
        {"name": "Telegram", "icon": "brand-telegram", "url": "https://t.me/Garan_Marine_Group_LLC"},
        {
            "name": "WhatsApp",
            "icon": "brand-whatsapp",
            "url": "https://wa.me/message/TAAPY7XJJZE2J1",
        },
    ],
    "refund_window_days": 14,
    "refund_processing_days": 3,
    "course_access_period": "12 months from enrollment",
    # LRQA Certificate of Approval, опубликован на meridiani.ge/recognitions/.
    "partner_iso": {
        "standard": "ISO 9001:2015",
        "body": "LRQA",
        "approval_number": "ISO 9001 – 00032550",
        "valid_until": "16 September 2027",
    },
}
