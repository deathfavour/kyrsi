# Kyrsi — образовательная платформа для моряков

Архитектура и модель данных описаны в [CLAUDE.md](CLAUDE.md).

## Стек

Django 6 + PostgreSQL + Django-шаблоны/htmx. Подробности — в CLAUDE.md.

## Локальный запуск

```bash
python -m venv venv
source venv/Scripts/activate   # Windows/Git Bash
pip install -r requirements-dev.txt

cp .env.example .env           # заполнить DATABASE_URL реальным Postgres
python manage.py migrate
python manage.py loaddata courses/fixtures/training_centers.json
python manage.py createsuperuser
python manage.py runserver
```

> В этом окружении локального PostgreSQL/Docker нет, поэтому `.env` временно
> указывает на sqlite (`DATABASE_URL=sqlite:///db.sqlite3`), чтобы можно было
> мигрировать и гонять тесты прямо сейчас. Как только будет доступен Postgres —
> переключить `DATABASE_URL` на `postgres://...` (см. `.env.example`), схема
> при этом не меняется.

## Команды

```bash
python manage.py runserver       # локальный запуск
python manage.py migrate         # миграции
celery -A config worker -l info  # фоновые задачи (нужен Redis; в .env этого окружения
                                  # CELERY_TASK_ALWAYS_EAGER=True — задачи идут синхронно без брокера)
pytest                           # тесты — гонять после каждого изменения
ruff check .                     # линт
```

> WeasyPrint требует нативные GTK/Pango/Cairo библиотеки, которых нет на чистом
> Windows. Импорт в `payments/pdf.py` сделан ленивым (внутри функции), чтобы
> их отсутствие не ломало весь проект (migrate/admin/тесты) — падает только
> реальная генерация PDF. См. `payments/tests/test_pdf.py` — тест skip'ается,
> если библиотек нет, вместо ложного падения.

Fondy — реальных merchant_id/secret_key/receiver_id в этом окружении нет (KYB не
пройден, см. CLAUDE.md, шаг 0), интеграция покрыта моками в `payments/tests/test_fondy.py`.

## Статус

- [x] Шаг 1 — каркас проекта + `courses` (TrainingCenter, Course, каталог, страница курса, admin)
- [x] Шаг 2 — `applications` (анкета кандидата, 4-шаговый флоу на htmx)
- [x] Шаг 3 — `payments` (Fondy split payments, webhook, Celery, PDF)
- [ ] Шаг 4 — `notifications`
- [ ] Шаг 5 — `refunds`
- [ ] Шаг 6 — `support`
- [ ] Шаг 7 — Excel-экспорт, django-auditlog, admin-полировка
- [ ] Шаг 8 — локализация, GDPR-тексты, security-хардening
