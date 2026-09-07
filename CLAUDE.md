# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Стартовый контекст для Claude Code. Основан на финальном ТЗ заказчика и архитектурных решениях, согласованных до старта кода. Архитектурные решения (раздел ниже) менять без явного запроса не нужно: это намеренные упрощения, не недосмотр.

---

## Что строим

Образовательная платформа для моряков: каталог 30–40 профессиональных курсов, покупка и регистрация кандидата, полный документооборот между тремя сторонами.

**Три стороны:**
- **Кандидат** — моряк, покупает курс.
- **Учебный центр** — проводит обучение, банк в Грузии (Батуми), расчёты в USD. Прямого доступа к сайту не имеет.
- **Официальный партнёр (наша компания)** — принимает оплату, удерживает комиссию, банк в Болгарии, расчёты в USD.

---

## Стек

- Backend: **Django** (Python) — готовая admin-панель, зрелые ORM/forms/security из коробки.
- БД: **PostgreSQL**.
- Frontend: **Django-шаблоны + htmx** (Alpine.js точечно). Без React/Vue/SPA — один деплоймент, без CORS и версионирования API.
- CSS: **Tailwind CSS через CDN** (`<script src="https://cdn.tailwindcss.com">` в `base.html`) — без Node-сборки/PostCSS-пайплайна, согласуется с «без сборки фронтенда». Если объём классов вырастет настолько, что CDN-версия начнёт заметно тормозить или потребуется кастомная конфигурация (тема, плагины) — тогда переходить на Tailwind CLI (генерация статического `.css` файла в `static/`), не раньше.
- Платежи: **Fondy** — специализируется на Восточной Европе и СНГ, поддерживает Болгарию (где зарегистрирован партнёр), имеет нативный split payments, принимает карты / Google Pay / Apple Pay. Интеграция через REST API + webhook (`fondy-python` или напрямую `requests`). **До старта интеграции уточнить у Fondy поддержку Грузии как получателя выплат** — от этого зависит выбор между реальным сплитом и B2B-сверкой (см. архитектурное решение ниже).
- Фоновые задачи: **Celery + Redis** — нужен с первого дня: документы генерируются через 15 минут после оплаты, не синхронно в webhook.
- Email: **Resend** или SendGrid.
- PDF-документы: **WeasyPrint** (HTML/CSS-шаблон → PDF).
- Excel-экспорт: **openpyxl**.
- Telegram: **python-telegram-bot**.
- WhatsApp: **WhatsApp Business API** — явно в ТЗ, но требует верификации бизнеса в Meta; закладываем интерфейс уведомлений абстрактным, реализацию — отдельным этапом.
- Тесты: **pytest + pytest-django**, с первого коммита.
- Локализация: **django-modeltranslation** для текстовых полей курса.
- Аудит-лог: **django-auditlog** — журнал всех значимых действий (требование ТЗ + ISO 9001).
- Хостинг: Render / Railway / Hetzner, EU-регион (GDPR + банк партнёра в Болгарии); свой домен, SSL автоматически.

---

## Архитектурные решения — намеренные упрощения

**Реальный автосплит через Fondy Split Payments API.**
Грузия подтверждена как получатель выплат у Fondy. Реализуем настоящий сплит: при каждой оплате Fondy автоматически делит платёж между двумя получателями.

Схема расчёта (обновлено 2026-08-24, реальные цены от заказчика — см. «Прайсинг курсов» ниже):
```
Кандидат платит: total_amount = Course.price_usd  (заказчик называет "GMG Academy")
Fondy переводит:
  → Учебный центр (Батуми, Грузия): course_price = Course.training_center_price_usd  ("MMTC")
  → Партнёр (Болгария):             commission_amount = price_usd − training_center_price_usd  ("GMG Margin")
```

**Важно: `price_usd` уже включает комиссию партнёра, наценка сверху при оплате не добавляется** —
это отличается от более ранней версии этого документа, где `total_amount = course_price +
commission_amount` (цена курса + комиссия сверху). Заказчик прислал прайс-лист в формате
MMTC / GMG Academy / GMG Margin, где GMG Academy (= `price_usd`, то, что видит и платит
кандидат) уже равен MMTC + Margin — уточнено явно, что на сайте показывается GMG Academy без
дополнительной надбавки.

Технически: при создании заказа Fondy передаём `split_rules` с двумя получателями — `receiver_id` учебного центра и партнёра, суммы вычисляются на бэкенде из `training_center_price_usd` и `price_usd`. Оба получателя заранее проходят KYB у Fondy и регистрируются как submerchants.

`Course.training_center_price_usd` — новое поле (миграция `0006_course_training_center_price_usd`), снэпшот доли учебного центра. `commission_percent` на Course остаётся в схеме (используется в admin/Excel для отображения %), но `payments/models.py::get_or_init_for_application` больше не читает его напрямую — `commission_amount` вычисляется как `price_usd − training_center_price_usd`. `commission_amount` и `course_price` на модели Payment — снэпшот на момент оплаты, не пересчитываются задним числом.

**TrainingCenter как модель, один сейчас.**
ТЗ требует «возможности нескольких партнёров и счетов в будущем» → создавай модель `TrainingCenter`, но на старте она содержит одну запись, заполненную через фикстуру. Не хардкодь реквизиты в settings. Так миграция к нескольким центрам не потребует переписывания схемы.

**Без аккаунта у кандидата.**
Заявка — анонимная форма по email/телефону. `User`/auth нужен только сотрудникам компании (Django staff) для входа в admin. Статус заявки кандидат отслеживает через email.

**USD как основная валюта.**
Обе стороны (учебный центр и партнёр) работают в USD. На курсе — `price_usd`. EUR оставляем как опциональное поле `price_eur` для будущего, но логику оплаты строим только на USD. Суммы на Payment — снэпшот на момент оплаты, изменение цены курса не пересчитывает старые инвойсы.

**Обычная Django admin.**
Wagtail и аналоги не нужны. 30–40 курсов + управление ценами/комиссиями — стандартная admin-панель закрывает всё это без второго слоя конвенций.

---

## Модель данных

**TrainingCenter** — `id`, `name`, `bank_name`, `bank_country`, `account_number`, `swift`, `currency` (default USD), `contact_email`, `is_active`.

**Course** — `id`, `slug` (unique), `training_center` (FK → TrainingCenter); `title`, `description`, `requirements` (мультиязычные через modeltranslation); `duration` (string), `course_dates` (text, nullable — даты проведения при наличии); `price_usd` (decimal), `price_eur` (decimal, nullable); `commission_percent` (decimal); `is_active` (bool).

**Application** (анкета кандидата) — `id`, `course` (FK → Course); `full_name`, `date_of_birth` (date), `citizenship`, `position`, `company` (nullable), `phone`, `email`, `comments` (text, nullable); `agreed_terms_at` (datetime — таймстамп согласия, доказательство для GDPR); `created_at`.

**ApplicationDocument** — `id`, `application` (FK → Application, related_name `documents`); `document_type` (seamans_book / certificate_of_competency / medical_certificate / passport / other); `file` (FileField, upload_to по application.pk); `uploaded_at`. Загрузка встроена в шаг 2 анкеты (см. референс-макет `ref-design/payment_tab1.png` — Seaman's Book и Certificate of Competency обязательны, остальное опционально). Файлы — часть документооборота, хранятся в media как и PDF-инвойсы (см. «Безопасность»), не удаляются.

**Payment** — `id`, `application` (FK → Application, one-to-one); `currency` (usd/eur); `course_price`, `commission_amount`, `total_amount` (decimal, снэпшот); `fondy_order_id` (unique, идентификатор заказа Fondy); `status` (pending / paid / failed / refunded); `invoice_number` (unique); `paid_at`.

**RefundRequest** — `id`, `payment` (FK → Payment); `reason` (text); `status` (pending / approved / rejected / completed); `requested_at`, `resolved_at` (nullable); `resolved_by` (FK → User, nullable); `notes` (text, nullable). При создании — автоуведомления учебному центру, партнёру, бухгалтерии.

**SupportTicket** — `id`, `ticket_type` (question / refund_request); `applicant_name`, `applicant_email`, `applicant_phone` (nullable); `related_payment` (FK → Payment, nullable); `message` (text); `status` (open / in_progress / closed); `created_at`. При создании — автоуведомления всем заинтересованным сторонам.

---

## Флоу покупки (4 шага)

1. **Страница курса** — название, описание, продолжительность, стоимость, требования, даты.
2. **Анкета кандидата** — заполнение формы (создаёт `Application`).
3. **Подтверждение условий** — четыре обязательных чекбокса (все четыре обязательны, без них кнопка оплаты неактивна):
   - согласие с условиями покупки;
   - согласие с политикой возврата средств;
   - согласие с обработкой персональных данных (GDPR);
   - подтверждение, что компания является официальным представителем учебного центра.
4. **Оплата через Fondy** — карта / Google Pay / Apple Pay (создаёт `Payment`, привязанный к `Application`). Редирект на Fondy Checkout или встроенная форма через Fondy JS SDK.
5. Страница подтверждения + PDF-инвойс + инструкции о дальнейших шагах.

---

## После успешной оплаты (callback от Fondy → Celery task, задержка 15 мин)

Fondy отправляет два типа уведомлений: `server_callback_url` (POST на бэкенд, основной) и `response_url` (редирект браузера на страницу успеха). Использовать `server_callback_url`. Webhook немедленно: верифицирует подпись Fondy, обновляет `Payment.status = paid`, ставит задачу в очередь Celery.

Через 15 минут Celery-таск:

- **Кандидату** (email) — письмо-подтверждение + PDF-инвойс + инструкции.
- **Учебному центру** (email) — анкета кандидата + подтверждение оплаты.
- **Партнёру/нашей компании** (email + Telegram) — уведомление о новой регистрации + инвойс комиссии.
- **Бухгалтерии** (email) — уведомление об оплате + размер комиссии + данные для учёта.

Если `paid_at` приходится на выходной (сб/вс), кандидату дополнительно:
> «Ваша заявка успешно зарегистрирована. Учебный центр свяжется с вами в первый рабочий день.»

---

## Документы

Генерируются через WeasyPrint (HTML/CSS → PDF):
- **Кандидату**: инвойс на полную сумму (стоимость курса + сервисный сбор).
- **Учебному центру**: подтверждение регистрации + анкета кандидата.
- **Партнёру**: инвойс комиссии (отдельный документ).

Excel-экспорт (openpyxl) — из admin-панели: список заявок, список платежей, журнал операций. Формат заранее согласовать с бухгалтерией заказчика (открытый вопрос).

---

## Модуль возврата (app: refunds)

- Кандидат подаёт заявку через кнопку Support → «Запросить возврат».
- Создаётся `RefundRequest`, автоматически уведомляются все стороны.
- Срок возврата — до 3 рабочих дней (фиксируется в публичной политике на сайте).
- Возврат через Fondy Refund API — ручной тригер сотрудника из admin, не автоматический.
- Все действия фиксируются в `RefundRequest` и django-auditlog.

---

## Служба поддержки (app: support)

Кнопка Support доступна на каждой странице. Два действия:

- **Задать вопрос** → создаёт `SupportTicket(type=question)`, уведомление сотруднику компании.
- **Запросить возврат** → редирект на форму `RefundRequest` или создаёт `SupportTicket(type=refund_request)`.

Каждое обращение автоматически уведомляет учебный центр, партнёра и бухгалтерию согласно типу тикета.

---

## Безопасность и соответствие стандартам

- **GDPR**: согласие с таймстампом в `Application.agreed_terms_at`; политика хранения данных — явный текст на сайте; право на удаление данных — ручная процедура через admin.
- **SSL**: автоматически на выбранном хостинге (Let's Encrypt).
- **django-auditlog**: журнал всех значимых действий — требование ТЗ и ISO 9001 / MLC-аудита.
- **Резервное копирование**: настроить на уровне хостинга (ежедневный snapshot БД).
- **Защита от мошенничества**: требует уточнения у Fondy (см. «Открыто») — формулировка про Stripe Radar осталась от черновика ТЗ до перехода на Fondy и неверна.
- **ISO 9001 / MLC**: для соответствия достаточно полного аудит-лога операций и сохранения всех PDF-документов с привязкой к платежу. Хранить PDF в медиа-папке, не удалять.

---

## Архитектура кода (что уже реализовано)

Django-проект называется `config` (не `kyrsi`) — `config/settings.py`, `config/urls.py`. Каждое доменное приложение из «Рекомендуемого порядка разработки» — отдельный top-level Django app (`courses`, далее `applications`, `payments`, ...), подключается в `INSTALLED_APPS` и через `include()` в `config/urls.py`.

**Настройки через `django-environ`.** Всё конфигурируемое читается из `.env` (`config/settings.py` вызывает `environ.Env.read_env`), а не хардкодится. `.env.example` — эталон под PostgreSQL (реальный БД проекта). Рабочий `.env` в этом окружении временно указывает на sqlite (`DATABASE_URL=sqlite:///db.sqlite3`), потому что локального Postgres/Docker нет — переключение на Postgres делается только правкой `DATABASE_URL`, без изменения кода или схемы.

**Локализация.** `modeltranslation` должен стоять в `INSTALLED_APPS` до `django.contrib.admin`. Мультиязычные поля модели регистрируются в `<app>/translation.py` (см. `courses/translation.py`) — после добавления/изменения таких полей обязательно `makemigrations`, иначе `title_en`/`title_ru` и т.п. не попадут в схему. Список языков — `LANGUAGES` + `MODELTRANSLATION_LANGUAGES` в settings (сейчас `en`, `ru` — заглушка, финальный список см. «Открыто»). Admin для моделей с переводом наследуется от `modeltranslation.admin.TranslationAdmin`, а не от `admin.ModelAdmin`.

**Шаблоны.** Общий `templates/base.html` в корне проекта (htmx уже подключён через CDN на будущее для htmx-флоу заявки). Шаблоны конкретного приложения — в `<app>/templates/<app>/...` (namespaced по конвенции Django), например `courses/templates/courses/course_list.html`.

**Тесты.** `pytest` + `pytest-django`, конфиг в `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings`). Тесты приложения лежат в `<app>/tests/` как пакет (`test_models.py`, `test_views.py`, ...), а не в одном `tests.py` — при добавлении новых доменных сущностей продолжай эту структуру.

**Фикстуры.** Данные, которые «намеренно одна запись сейчас» (см. `TrainingCenter` в разделе «Архитектурные решения»), загружаются через `<app>/fixtures/*.json` + `loaddata`, не через хардкод в коде или ручное создание в admin.

**Wizard-флоу (`applications`).** Каждый шаг — отдельная view + partial-шаблон
(`_step_*.html`), обёрнутый в `applications/templates/applications/wizard.html`.
View определяет htmx-запрос по заголовку `HX-Request` (`_is_htmx`/`_render_step`
в `applications/views.py`) и либо возвращает только partial (свап `#wizard-step`),
либо полную страницу — так каждый шаг работает и как htmx-свап, и как отдельный URL.
Переход между шагами, требующими нового объекта в БД (например, после шага 3 —
на реальную страницу оплаты), сделан через `redirect()` (PRG), а не рендером
следующего шага прямо в POST-хендлере — htmx корректно следует за 302 и подменяет
контент финальным GET-ответом.

**Payment — один снэпшот на Application.** `Payment.objects.get_or_init_for_application()`
(`payments/models.py`) — единая точка создания: если платежа ещё нет, считает
`course_price`/`commission_amount`/`total_amount` от текущих `Course.price_usd`/
`commission_percent` и сохраняет их как снэпшот; повторный вызов для той же
`Application` просто возвращает существующий `Payment` (OneToOne, идемпотентно).
Смена цены курса после этого момента на уже созданный `Payment` не влияет.
`fondy_order_id` перегенерируется через `payment.refresh_fondy_order_id()` перед
повторной попыткой оплаты (Fondy не даёт переиспользовать order_id из проваленной сессии).

**Fondy-клиент (`payments/fondy.py`).** Вся интеграция изолирована в одном модуле:
`_signature()`/`verify_signature()` (sha1 по отсортированным значениям параметров,
см. код) и `_build_split_rules()`. ⚠️ Точные названия полей `split_rules` — по
документированному формату Fondy Split Payments, но **не подтверждены на реальном
тестовом платеже** (KYB ещё не пройден, см. шаг 0) — сверить с аккаунт-менеджером
Fondy при первой реальной интеграции. `payments/tests/test_fondy.py` мокает
`requests.post`, реальных сетевых вызовов в тестах нет.

**WeasyPrint — ленивый импорт.** `payments/pdf.py` импортирует `weasyprint` **внутри
функции** `html_to_pdf()`, а не на уровне модуля. Причина: WeasyPrint требует нативные
GTK/Pango/Cairo библиотеки, которых на многих машинах (в т.ч. в этом Windows-окружении)
просто нет — импорт на уровне модуля роняет весь Django-проект (migrate, admin, любой
`manage.py`), а не только генерацию PDF. Не убирай отложенный импорт без проверки, что
нативные библиотеки гарантированно доступны в целевом окружении. `payments/tests/test_pdf.py`
делает реальный вызов и `pytest.skip()`, если библиотек нет — остальные тесты мокают
`payments.tasks.html_to_pdf`.

**Celery-таск как единая точка после оплаты.** `payments/tasks.py::process_paid_payment`
ставится в очередь из `payments/views.py::fondy_webhook` через
`.apply_async(countdown=15*60)` — задержка обязательна (см. «После успешной оплаты»),
не убирать. Локально/в тестах при отсутствии Redis используй `CELERY_TASK_ALWAYS_EAGER=True`
(уже включено в `.env` этого окружения) — тогда `apply_async` выполняет таск синхронно
в том же процессе, без брокера. В тестах на сам `process_paid_payment` таск вызывается
как обычная функция (`process_paid_payment(payment.pk)`), не через `.delay()`.

**Retry + логирование сбоев (2026-08-18, найдено при сквозном golden-path прогоне).**
`fondy_webhook` вызывает `process_paid_payment.apply_async(...)` без `.get()` — до этого
изменения любое исключение внутри таска (PDF-рендер, отправка email) молча пропадало:
webhook всё равно отвечал Fondy "OK", а PDF/уведомления просто не появлялись, без единого
сигнала об ошибке где-либо. Подтверждено вживую: в этом Windows-окружении WeasyPrint не
может загрузить нативные библиотеки (см. выше), и весь пост-оплатный флоу тихо не
выполнялся при реальном прогоне через webhook. Исправлено — `@shared_task` теперь
с `autoretry_for=(Exception,)` (до 5 попыток, экспоненциальный backoff 60–600с,
джиттер) на случай временных сбоев (email/PDF backend недоступны на 1 попытке), плюс
`try/except Exception: logger.exception(...); raise` вокруг тела таска — финальный
(или любой промежуточный) отказ теперь как минимум попадает в логи с `payment_id`,
прежде чем исключение продолжит путь наверх к Celery. Прямой вызов
`process_paid_payment(pk)` в тестах не запускает retry-обёртку Celery (retry активен
только через полноценный task-протокол `.apply()`/`.delay()`/worker), так что
существующий паттерн вызова в тестах не менялся.

**Уведомления партнёру/бухгалтерии — email settings, не модель.** В отличие от
`TrainingCenter` (модель, т.к. центров может стать несколько), партнёр и бухгалтерия
— единственные и не описаны в «Модели данных», поэтому их email/Telegram-реквизиты
— настройки (`PARTNER_NOTIFICATION_EMAIL`, `ACCOUNTING_EMAIL`, `TELEGRAM_BOT_TOKEN`/
`TELEGRAM_CHAT_ID`), а не поля БД.

**`notifications` app (шаг 4) — абстрактный канал уведомлений, без моделей.**
`notifications/backends.py::NotificationBackend` — общий интерфейс (`send_message`,
`send_email`) с тремя реализациями: `EmailBackend` (обёртка над
`EmailMultiAlternatives` — текст + HTML + PDF-вложения), `TelegramBackend`
(перенесённый из `payments/telegram.py::send_telegram_message`, тот же контракт:
просто исходящий POST, не интерактивный бот), `WhatsAppBackend` (заглушка-no-op —
WhatsApp Business API не реализован, требует верификации бизнеса в Meta, см. «Открыто»).
Полноценный интерактивный Telegram-бот (команды, FAQ-матрица) **не входит** в этот шаг —
в ТЗ он упомянут без деталей поведения, реализация ждёт уточнений от заказчика.

`notifications/services.py` — четыре высокоуровневые функции
(`notify_candidate_paid`, `notify_training_center_paid`, `notify_partner_paid`,
`notify_accounting_paid`), которые `payments/tasks.py::process_paid_payment` вызывает
вместо прежних f-строк напрямую в таске. Каждая функция рендерит HTML+текстовую пару
шаблонов из `notifications/templates/notifications/email/*.{html,txt}` через
`_render_email()` и уходит в `EmailBackend`; `notify_partner_paid` дополнительно
шлёт `TelegramBackend.send_message()`. Русская формулировка про «первый рабочий день»
(см. «После успешной оплаты») теперь живёт в `candidate_payment_confirmation.{html,txt}`,
не в Python-константе — если меняешь текст, редактируй оба файла (html и txt) синхронно.

---

## Команды

```bash
# окружение (Windows/Git Bash; на venv/Scripts вместо venv/bin)
python -m venv venv
source venv/Scripts/activate
pip install -r requirements-dev.txt   # включает requirements.txt + pytest/ruff

# БД
python manage.py migrate
python manage.py loaddata courses/fixtures/training_centers.json   # одна запись TrainingCenter (Батуми)
python manage.py createsuperuser

python manage.py runserver            # localhost:8000, каталог курсов на "/", admin на "/admin/"

pytest                                # весь набор тестов
pytest courses/tests/test_models.py   # один файл
pytest courses/tests/test_models.py::test_course_str   # один тест
ruff check .                          # линт (миграции исключены из проверки)

python manage.py makemigrations <app> # после изменения моделей — включая modeltranslation-поля
```

`celery -A config worker -l info` нужен для реальной асинхронной обработки; при `CELERY_TASK_ALWAYS_EAGER=True` (как в `.env` этого окружения — тут нет Redis) задачи выполняются синхронно без брокера.

---

## Рекомендуемый порядок разработки

Модулями, коммит после каждого шага:

0. **⚠️ До старта платёжного модуля** — учебный центр (Грузия) и партнёр (Болгария) проходят KYB у Fondy и регистрируются как submerchants. Без `receiver_id` обоих сторон split_rules не собрать. Разработка курсов и заявок идёт параллельно — не блокирует.
1. ✅ Каркас проекта + `courses` app (TrainingCenter, Course, каталог, страница курса, admin).
2. ✅ `applications` app (анкета кандидата, 4-шаговый флоу на htmx).
3. ✅ `payments` app (Fondy split payments, webhook, Celery-таск, PDF через WeasyPrint).
4. ✅ `notifications` app (HTML/text email-шаблоны, `NotificationBackend` абстракция
   email/Telegram/WhatsApp). Интерактивный Telegram-бот (команды, FAQ-матрица) и
   реальная реализация WhatsApp **не входят** — обе остаются открытыми вопросами
   до уточнений от заказчика (см. «Открыто»).
5. ✅ **Вёрстка по `ref-design/` (2026-08-18).** Golden path (курсы → заявка → оплата →
   success) работал функционально с шага 3, но шаблоны были голым скелетом без
   стилизации. `ref-design/*.png` подтверждён заказчиком как эталон 1:1 (см.
   «UX-требования и бренд» выше). Единственное исключение — платёжные лого на
   `payment_tab2.png` (Stripe/Visa SecureCode в макете — плейсхолдер; в вёрстке
   заменены на текстовые ярлыки VISA/Mastercard/Apple Pay/Google Pay, без брендинга
   Stripe — провайдер остаётся Fondy).

   Свёрстано: `base.html` (header/footer/Tailwind CDN), `courses/home.html` (landing,
   `/`), `courses/course_list.html` (каталог, `/courses/`), `courses/course_detail.html`
   (страница курса по `course-preview.jpg`), весь чекаут-wizard (`wizard.html` с
   3-стадийным progress bar, `_step_form.html`/`_step_confirm.html`/`_step_payment.html`
   по `payment_tab1.png`/`payment_tab2.png`), `payments/success.html` по
   `transation_success.png`.

   **4 backend-шага, 3 визуальных стадии.** Макеты показывают 3-шаговый progress bar
   (Application Form → Purchasing → Online Course) без отдельного экрана под 4
   обязательных чекбокса согласия из ТЗ. Решение (2026-08-18): backend остаётся
   4-шаговым (`apply_form` → `apply_confirm` → `apply_payment` → `success`, см.
   `applications/views.py`), но `wizard.html` визуально схлопывает шаги 2 и 3
   («форма» и «confirm») в первую стадию «Application Form» — `step<=3` подсвечивает
   первый узел прогресс-бара. Не убирать шаг подтверждения чекбоксов — это требование
   ТЗ, макет просто не показывает его как отдельную стадию.

   **Маршруты изменились**: `/` теперь landing (`courses:home`), каталог курсов
   переехал на `/courses/` (`courses:course_list`), `/courses/<slug>/` без изменений.

   **`courses/templatetags/course_extras.py`** — `Course.description`/`requirements`
   хранятся как единый текст с секциями-разделителями (`"What You Will Learn:\n"`,
   `"Why This Course Matters:\n"`, `"Career Value:\n"`, `"Recommended for: ..."`) —
   так их собрала фикстура `courses.json` (см. «Каталог курсов» выше), отдельных полей
   под это в модели нет. `parse_course_description`/`recommended_for` — template
   filters, разбирающие текст обратно на секции для вёрстки по макету (три карточки
   Why Take/You Will Learn/Career Value + список ролей). Если текст без разделителей —
   весь уходит в `overview`, страница не падает.
   **`recommended_for(course)` — fallback по `category`, не просто парсинг.** У 26 из
   53 курсов `requirements` пустое (в `Course_Description.docx` не было секции
   "Recommended for" для этих курсов) — `course-preview.jpg` показывает карточку
   "Who Is This Course For?" всегда, поэтому вместо скрытия блока при пустых данных
   фильтр отдаёт общий список ролей по `course.category`
   (`_FALLBACK_RECOMMENDED_FOR` — navigators/engineers). Не подтверждено заказчиком
   per-course, тот же статус, что и `level`/`category`/`topic`/`instructor` (см.
   «Открыто»).
   **`parse_course_description` — тот же fallback-паттерн для `why_matters`/
   `career_value`.** 22 и 26 из 53 курсов соответственно не имеют секций "Why This
   Course Matters:"/"Career Value:" в описании — обе карточки в макете показываются
   всегда, поэтому пустые значения подменяются общим текстом
   (`_FALLBACK_WHY_MATTERS`/`_FALLBACK_CAREER_VALUE`), а не скрывают карточку.
   Тоже not customer-confirmed placeholder-копирайтинг, не реальный текст под
   конкретный курс.

   **Раунд 2 (2026-08-18, тот же день): полная перестройка под 1:1, включая
   расширение модели.** Первый проход (выше) сознательно пропускал блоки без данных
   в схеме — по итогам ревью с заказчиком (пришли 5 новых макетов:
   `online_courses.jpg`, `our_services.jpg`, `abous_us.jpg`, `author.jpg`,
   `contact_us.jpg`) решено расширить модель вместо того, чтобы урезать вёрстку:

   - `Course` получил `level` (beginner/intermediate/advanced), `category`
     (navigators/engineers — бейдж «FOR NAVIGATORS/FOR ENGINEERS»), `topic`
     (6 значений: Navigation & Bridge/Safety & Compliance/Cargo Operations/
     Ship Handling/Regulations/Environmental — вкладки на `/courses/`),
     `instructor_name`/`instructor_bio`, `original_price_usd` (опциональная
     старая цена для скидочного бейджа). Миграции `0004_course_category_...`,
     `0005_course_topic`.
   - **Ни одно из этих полей не было в `Course_Description.docx`/`Course_Prices.docx`**
     — заполнены вручную для всех 53 курсов по реальному предмету курса (не
     эвристикой/автоматикой — первая попытка с keyword-эвристикой дала явно
     неверные результаты для универсальных курсов типа First Aid/Stress
     Management, пришлось пересверить руками). Инструктор — обобщённый
     placeholder на всю категорию («Marine Engineering Expert» / «Navigational
     Systems Expert»), без фото и без реальной привязки к конкретному человеку.
     **Не авторитетно** — заказчик не подтверждал level/category/topic/instructor
     per-course, уточнить и поправить в admin при первой возможности.
   - `courses/templates/courses/course_detail.html` переписан целиком: badge
     категории, hero-фото + 4 миниатюры (градиенты-плейсхолдеры, не настоящие
     фото), 5 feature-иконок (Duration/Level/Language/Certificate/Access), цена
     со скидкой (`Course.has_discount`/`discount_percent`), Instructor-карточка,
     Course Includes, compliance-бар, CTA-баннер с payment-логотипами внизу.
   - Новая страница `/courses/` (`course_list.html`) — hero-карусель из 4 **реальных**
     курсов каталога (не выдуманных промо-сюжетов вроде «U.S. Coast Guard
     Standards» из макета), category-кнопки (Navigators/Engineers), 6 topic-вкладок
     + текстовый поиск — всё на Alpine.js `x-data` без htmx (все 53 курса
     отдаются одним запросом, фильтрация на клиенте), карточка курса вынесена в
     переиспользуемый `_course_card.html`.
   - **Новое приложение `pages`** (без моделей — чисто статический контент):
     `/our-services/`, `/about-us/`, `/contact-us/`. Contact-форма — HTML без
     backend (просто вёрстка, не отправляет письма — заказчик подтвердил, что
     это ожидаемо на этом этапе; реальная отправка — предмет будущего тикета).
     About Us содержит **реальные подтверждённые данные заказчика**: имена
     основателей (Vadym Milutchenko — Garant Marine Group, Capt. Zaza Avaliani —
     Meridian), адрес головного офиса (16a Bagrationi St, Batumi, Georgia),
     контакты (`info@garantunitedacademy.com`, `support@garantunitedacademy.com`,
     `bd@garantmarinegroup.com`) — подтверждено заказчиком как публикуемые.
   - Навигация в `base.html` приведена к варианту, повторяющемуся на 6 из 7
     макетов (Online Courses / Author Courses of GUA / About Us / Our Services /
     Contact), а не к варианту с `home_page.png` (там другой набор пунктов —
     видимо более ранний черновик). Кнопка LOGIN из макета убрана — у кандидата
     нет аккаунта по архитектуре (см. «Без аккаунта у кандидата» выше), некуда вести.
   - **"Author Courses" — реализовано отдельным app'ом (2026-08-18, третий раунд
     вёрстки).** Ранее откладывалось до архитектурного решения — решение принято:
     новое top-level приложение `author_courses` (не расширение `courses.Course`,
     см. предыдущую заметку почему) с двумя моделями, `AuthorCourse` и
     `CareerPathProgram` (оба — `slug`/`title`/`description`/`duration`/`category`
     navigators-engineers/`price_usd`/`is_active`/`order`; `AuthorCourse`
     дополнительно `level`). Один view `author_course_list` без detail-страниц —
     макет `author.jpg` не показывает переход на отдельную страницу курса, только
     список с категорийным фильтром (Alpine `x-data`, тот же паттерн что
     `courses/course_list.html`). Consulting-блок (Technical Consultation $250 /
     Free Consultation) — статический контент в шаблоне, не модель (аналогично
     `pages/our_services.html` — единственный, не варьируется по курсу).
     Admin — обычный `ModelAdmin` (не `TranslationAdmin`, локализация полей сюда
     не заведена — тот же нерешённый статус, что и у `Course`, см. «Открыто»).
     `author_courses/fixtures/author_courses.json` — 12 `AuthorCourse` (6
     navigators по названиям из макета + 6 engineers, симметричный demo-набор,
     т.к. макет показывает только вкладку navigators) и 8 `CareerPathProgram`
     (4+4, тот же принцип). **Все цены/длительности/описания — demo-данные,
     скопированные из/по аналогии с `author.jpg`, не подтверждены заказчиком** —
     как и `Course.level`/`category`/`topic`/`instructor`, тот же статус (см.
     «Открыто»). Картинки карточек переиспользуют уже загруженные темы из
     `static/img/` (`author_courses/templatetags/author_course_extras.py` —
     dict по `slug`, т.к. у `AuthorCourse` нет `topic`-поля как у `Course`).
     Пункт меню "Author Courses of GUA" в `base.html` (хедер и футер) теперь
     ведёт на `author_courses:author_course_list` вместо мёртвого `href="#"`.

   **Стилизация Django-форм — через `widget.attrs["class"]` в `forms.py`, не в
   шаблоне.** `{{ field }}` рендерит инпут с классами, заданными в виджете (см.
   `applications/forms.py::_INPUT_CLASSES`/`_FILE_INPUT_CLASSES`) — шаблон просто
   перебирает `{% for field in form %}` и выводит `{{ field }}`/`{{ field.label }}`
   без ручной разметки `<input>`. Единообразный паттерн для новых форм
   (`refunds`/`support`) — не переключаться на `{{ form.as_p }}` (теряет Tailwind-стили
   и не позволяет собственный grid-layout) и не использовать `django-widget-tweaks`
   (лишняя зависимость, когда `attrs` в виджете уже решает задачу).

   **`{# ... #}` не поддерживает переносы строк** — Django однострочный комментарий
   рвётся посреди многострочного текста и утекает в HTML-вывод как обычный текст (был
   баг на этом в `wizard.html` при первой вёрстке). Для многострочных заметок в
   шаблонах использовать `{% comment %}...{% endcomment %}`.
6. ✅ **`refunds` app (2026-08-18).** `RefundRequest` (payment FK, reason,
   status pending/approved/rejected/completed, requested_at, resolved_at,
   resolved_by, notes) — модель 1:1 по CLAUDE.md. Кандидат подаёт заявку через
   `refunds/request/` (`RefundRequestForm` — без аккаунта находит свой `Payment`
   по `invoice_number` + `email`, а не выбором из списка, тот же принцип, что и
   `applications`; отклоняет, если платёж не в статусе `paid`). При создании —
   `notify_refund_requested()` (`notifications/services.py`) уведомляет учебный
   центр/партнёра/бухгалтерию email'ом (кандидат не уведомляется здесь отдельно —
   видит confirmation прямо на странице после сабмита). **Возврат через Fondy —
   ручной admin action** `RefundRequestAdmin.approve_and_process_refund`, не
   автоматический (по требованию CLAUDE.md): вызывает `payments/fondy.py::
   refund_payment()` (новая функция, Fondy Reverse API, тот же
   sha1-signature-паттерн что `create_checkout_url`; ⚠️ формат ответа не
   подтверждён на реальном платеже — тот же caveat, что у `_build_split_rules`,
   см. шаг 0), при успехе переводит `RefundRequest.status = completed` и
   `Payment.status = refunded`; при `FondyError` — статус не меняется, ошибка
   в admin message. Отдельный action `reject_request` для отказа без Fondy-вызова.
   Ссылка "Request a Refund" добавлена в футер (`base.html`, рядом с Refund
   Policy) как временная точка входа — полноценная кнопка Support с двумя
   действиями (Задать вопрос / Запросить возврат) появится в шаге 7, не
   дублировать этот функционал там, просто подключить существующую форму.
   django-auditlog ещё не подключен (шаг 8) — фиксация действий в
   `RefundRequest.resolved_by`/`resolved_at` есть, полноценный журнал позже.
7. ✅ **`support` app (2026-08-18).** `SupportTicket` — 1:1 по CLAUDE.md
   (ticket_type question/refund_request, applicant_name/email/phone,
   related_payment FK nullable, message, status open/in_progress/closed).
   **Кнопка Support — плавающая кнопка внизу справа на каждой странице**
   (`templates/base.html`, Alpine.js dropdown, `@click.outside`/`@keydown.escape`
   для закрытия), с двумя пунктами: "Ask a Question" → `support:ask_question`
   (`SupportQuestionForm`, создаёт `SupportTicket(type=question)`, без выбора
   типа — форма сама проставляет `ticket_type` в `save()`) и "Request a Refund"
   → прямая ссылка на уже существующий `refunds:request_refund` (не дублирует
   форму возврата через `SupportTicket(type=refund_request)` — CLAUDE.md
   формулирует это как "или", реализован путь через отдельный `refunds` app,
   т.к. он уже даёт более структурированный флоу с поиском Payment по invoice+email;
   `SupportTicket.TicketType.REFUND_REQUEST` остаётся в модели/уведомлениях
   для полноты API и на случай, если понадобится создавать такие тикеты
   из другого места, но текущий UI туда не ведёт).
   **`notify_support_ticket_created()`** (`notifications/services.py`) — получатели
   зависят от `ticket_type`: `question` уведомляет только
   `PARTNER_NOTIFICATION_EMAIL` (сотрудник поддержки, см. CLAUDE.md "уведомление
   сотруднику компании"), `refund_request` с `related_payment` уведомляет все
   три стороны (training center/partner/accounting), как `notify_refund_requested`.
   Ссылка "Request a Refund" в футере (добавленная в шаге 6) остаётся —
   плавающая кнопка не заменяет её, это два равноценных входа в одну форму.
8. ✅ **Excel-экспорт + django-auditlog (2026-08-18).**
   **`config/excel_export.py::export_queryset_to_xlsx(queryset, columns, filename)`**
   — общая утилита (не доменная модель, поэтому в `config/`, не в отдельном app):
   `columns` — список `(header, accessor)`, `accessor` — `callable(obj) -> value`.
   Timezone-aware datetime (весь проект на `USE_TZ=True`) приводятся к naive
   через `_excel_safe()` — openpyxl иначе падает с `TypeError` (Excel не знает
   про tz). Подключена как admin action `export_to_excel` в
   `ApplicationAdmin`/`PaymentAdmin`/`RefundRequestAdmin` — колонки подобраны
   вручную по разумному дефолту (все значимые поля модели), **формат НЕ
   согласован с бухгалтерией заказчика** (см. «Открыто» — это осталось открытым
   вопросом, экспорт уже существует и рабочий, но колонки/порядок могут
   измениться при получении реального формата от заказчика).
   **django-auditlog** зарегистрирован через `AppConfig.ready()` в каждом app
   (`courses` → Course/TrainingCenter, `applications` → Application, `payments`
   → Payment, `refunds` → RefundRequest, `support` → SupportTicket) —
   `auditlog.registry.auditlog.register(Model)`, не через `@auditlog.register()`
   декоратор на классе (модели уже определены до этого шага, трогать
   `models.py` ради декоратора избыточно). `AuditlogMiddleware` в
   `MIDDLEWARE` привязывает `LogEntry.actor` к текущему admin-пользователю.
   Таблица `auditlog_logentry` — единый журнал по всем пяти моделям, доступен
   в admin автоматически (auditlog регистрирует свой `LogEntryAdmin`).
9. ✅ **Локализация (инфраструктура) + GDPR-тексты + security-хардening
   (2026-08-18).**
   **Локализация — только инфраструктура, без перевода** (осознанное решение,
   см. «Открыто»: список языков сайта не подтверждён заказчиком, придумывать
   его самостоятельно не стали). `modeltranslation` был уже подключён
   (`courses/translation.py`, `_en`/`_ru` поля в схеме), но language switcher
   в header был мёртвым текстом "EN", не переключающим язык. Исправлено:
   `path("i18n/", include("django.conf.urls.i18n"))` в `config/urls.py`
   (Django's встроенный `set_language` view) + рабочий dropdown в
   `templates/base.html` (`{% get_available_languages %}`, POST-форма на
   `{% url 'set_language' %}` с `next=request.path` для каждого языка). Сам
   контент (`title_ru`/`description_ru` и т.п.) остаётся пустым — переключение
   между EN/RU теперь технически работает, но на RU просто нечего показывать,
   пока не придёт текст от заказчика.
   **GDPR/юридические тексты — новый app `legal`** (без моделей, как `pages`):
   `/terms/`, `/privacy-policy/`, `/refund-policy/`. Все три — placeholder-текст
   с явным жёлтым баннером наверху страницы ("не проверено юристом" / для
   refund policy — "условия возврата ещё не согласованы с заказчиком"), не
   выдуманный от лица заказчика юридический документ. Privacy Policy отдельно
   помечает data retention period как неопределённый (см. «Открыто» — та же
   формулировка). Ссылки на эти страницы, ранее `href="#"`, подключены в
   footer (`base.html`) и во всех трёх местах, где раньше было упоминание
   "Privacy Policy"/"Terms & Conditions" без ссылки: `applications/wizard.html`
   (IMPORTANT INFORMATION блок), `applications/_step_form.html` (декларативный
   чекбокс), `pages/contact_us.html` (форма обратной связи).
   **Security-хардение** (`config/settings.py`, конец файла) — блок
   `if not DEBUG:` с `SECURE_SSL_REDIRECT`/`SESSION_COOKIE_SECURE`/
   `CSRF_COOKIE_SECURE`/`SECURE_HSTS_*`/`SECURE_CONTENT_TYPE_NOSNIFF`/
   `X_FRAME_OPTIONS=DENY` — гейтится на `DEBUG`, чтобы локальная разработка
   по HTTP не сломалась (SSL сам по себе — с хостинга, см. «Стек», эти
   настройки просто требуют его и реагируют на редиректы/куки правильно).
   `CSRF_TRUSTED_ORIGINS` — новый env var (`.env.example` обновлён с
   комментарием), пустой по умолчанию, обязателен выставить на реальный домен
   при деплое. `python manage.py check --deploy` с `DEBUG=False` даёт только
   один warning — `SECRET_KEY` дефолт (ожидаемо, уже помечен
   "change-me-in-production", реальный ключ — через `.env`).

---

## UX-требования и бренд (добавлено 2026-08-18, из `ТЗ для IT.docx` + `ref-design/`)

Заказчик — **Garant United Academy** (GMG × Meridian Training Center), домены `garantunitedacademy.com`.
В коде и фикстурах «учебный центр» = Meridian Training Center, «партнёр» = GMG/Garant.

**`ref-design/*.png` — эталон вёрстки 1:1** (подтверждено заказчиком), не просто "принципы для вдохновения:
home page, страница курса, чекаут (2 экрана: анкета+документы → оплата), success-страница —
верстать по этим макетам максимально точно (лейаут, блоки, порядок секций, копирайтинг заголовков).
**Единственное исключение — платёжные лого**: макеты показывают Stripe/Visa SecureCode/PCI DSS,
это дизайнерский stock-плейсхолдер, реальный платёжный провайдер остаётся **Fondy** (см. «Стек» выше) —
при вёрстке `payment_tab2.png` заменить лого на Fondy/Visa/Mastercard/Google Pay/Apple Pay, текст и структуру формы оставить как в макете.

Ключевые UX-принципы поверх текущей архитектуры (не меняют модель данных, влияют на шаблоны/вёрстку следующих итераций):

- **Карточка курса без перехода** — цена, длительность, формат, лого признающих классификационных обществ и краткое summary видны сразу в каталоге; «Подробнее» разворачивает полное описание на месте или ведёт на страницу курса (см. `course-preview.jpg`). Цифры вида «N человек прошли курс» показывать только если это реальные данные — не показывать «0».
- **Фильтр по Rank и Vessel Type** в каталоге — приоритетная функция, реализовать до общего поиска по тексту.
- **Чекаут выглядит как единый экран** («1 экран, минимум шагов» в тексте ТЗ), но в макетах это всё equally тот же 3–4-шаговый прогресс-бар (Application → Purchasing → Course), просто без лишних промежуточных страниц-заглушек. Совместимо с текущим htmx wizard `applications` — по сути, не «убрать шаги», а не растягивать их на лишние переходы.
- **Блок доверия у кнопки оплаты** — ссылки на политику защиты данных и авторское право Meridian прямо возле CTA, не только в футере.
- **Mobile-first** — приоритет №1 по формулировке заказчика, тяжёлые десктоп-виджеты (карусели, Slider Revolution-подобные баннеры) избегать.
- **Маркетинговые триггеры** (эксклюзивность в заголовке, «осталось N мест», ценовой якорь «очный тренинг $X vs онлайн $Y», видео от инструктора) — контентный/маркетинговый слой поверх страницы курса, не влияет на backend-модели.

**ApplicationDocument (загрузка документов)** — добавлено в модель данных выше по референс-макету `payment_tab1.png`: Seaman's Book и Certificate of Competency обязательны, Medical Certificate / Passport / Other — опциональны, до 5MB, PDF/JPG/PNG.

**Каталог курсов** — `Course_Description.docx` и `Course_Prices.docx` вместе являются источником контента для всех курсов на сайте (description/requirements/duration из Description, price_usd из Prices). Использовать как источник для фикстуры `courses/fixtures/*.json` при сидинге каталога, не выдумывать курсы/описания/цены самостоятельно.

⚠️ **Списки не совпадают 1:1** (проверено 2026-08-18):
- `Course_Description.docx` содержит **~51 курс** с полными описаниями (Course Overview / You Will Learn / Why This Course Matters / Recommended For / Career Value) — по формату это то же, что в макете `course-preview.jpg`.
- `Course_Prices.docx` (Annex N1) даёt цену только **36 курсам** (2 строки таблицы пустые/разделители).
- Минимум 15 курсов из Description **не имеют цены** в Prices: STS Ship-to-Ship Transfer, Engine Room Management Simulator, First Aid (Heartsaver CPR/AED), Maritime Cyber Security, Media Response, Cross-Cultural Interpersonal Skills, Hatch Cover Inspection, Stress Management at Sea, Human Factors Management, Effective Communication Onboard, Operation of Crew Manning Agency, Fatigue Awareness & Management, High Pressure Air Compressor, Dual Fuel Marine Engine, Combating Oil Spills & Petroleum Product Response.
- Есть расхождения в названиях между двумя файлами: `Course_Prices` → «ECDIS Refreshing» ($300) vs `Course_Description` → «Passege plaining with ECDIS» (нет отдельной цены под этим именем); `Course_Prices` → «Shipboard Safety» ($150) vs `Course_Description` → «Shipboard Security» (полное описание, без явной цены под этим именем). Нужно уточнить у заказчика, это одна и та же пара курсов с опечаткой в названии или два разных курса.
- Итог по ТЗ «30–40 курсов» (см. «Что строим») формально совпадает с 36 из Prices, но не с 51 из Description.

**Решено (2026-08-18):** грузим все 51 курс в фикстуру. У 15 курсов без цены `price_usd = null` (поле уже nullable в схеме, миграция `0003_alter_course_price_usd`). На карточке/странице курса вместо цены показывать «Contact us for price» и **скрывать кнопку оплаты** (переход в чекаут/`ApplicationForm` недоступен, пока цена не проставлена в admin) — это не нарушает «цена сразу, без исключений» из ТЗ (цена либо видна, либо честно помечена как ещё не назначенная, никогда не скрыта под кнопкой). Как только заказчик пришлёт цену — просто проставить `price_usd` в admin, кнопка появится сама.

**Фикстура каталога загружена (2026-08-18):** `courses/fixtures/courses.json`, 53 записи (36 с ценой, 17 без — `price_usd = null`), проверено тестом `courses/tests/test_fixtures.py`. Решения по спорным парам названий (обсуждено с заказчиком):
- «Passage Planning with ECDIS» (описание) и «ECDIS Refreshing» $300 (цена, без своего описания — `description = "Description coming soon."`) заведены как **два разных курса**.
- «Shipboard Security» (описание, ISPS Code) и «Shipboard Safety» $150 (цена, без своего описания — `description = "Description coming soon."`) — тоже **два разных курса**.
- `duration = "TBD"` для «Train the Trainer», «Fatigue Awareness & Management», «ECDIS Refreshing» и «Shipboard Safety» (в тексте заказчика длительность не указана; последние два — те же price-only-стабы без описания, см. выше — изначально были заведены с `duration = ""`, из-за чего на странице курса иконка длительности показывала пустоту вместо текста, исправлено 2026-08-18 при сверке дизайна с `course-preview.jpg`).
- `commission_percent = 0.00` был временным placeholder для всех 53 курсов до согласования реального договора комиссии — **заменён реальными цифрами для 50 курсов 2026-08-24/25, см. «Прайсинг курсов» ниже.** Оставшиеся 3 курса без цены (`price_usd = null`) по-прежнему на `commission_percent = 0.00`, ждут согласованной цены от заказчика.
- Локализация: заполнены только `title_en`/`description_en`/`requirements_en` (плюс базовые поля = `LANGUAGE_CODE=en`), `_ru` пустые — перевод на русский предмет отдельного этапа 8 «Локализация» в порядке разработки, не делать самостоятельно без текста от заказчика.

**Прайсинг курсов — реальные данные от заказчика (2026-08-24).** Заказчик прислал таблицу
цен для 36 из 53 курсов (скриншот, формат MMTC / GMG Academy / GMG Margin). Применено:
- **MMTC → `Course.training_center_price_usd`** (новое поле, миграция
  `0006_course_training_center_price_usd`) — доля, уходящая Meridian Training Center.
- **GMG Academy → `Course.price_usd`** — итоговая цена, которую видит и платит кандидат на
  сайте. Подтверждено явно: наценки сверху при оплате нет, GMG Academy уже включает margin
  (см. «Архитектурные решения» выше — это изменило формулу в
  `payments/models.py::get_or_init_for_application`).
- **GMG Margin** — не хранится отдельным полем, вычисляется как `price_usd −
  training_center_price_usd` в момент создания Payment; `commission_percent` на Course
  пересчитан как `margin / price_usd * 100` для каждого из 36 курсов (для отображения в
  admin/Excel — сама формула Payment это поле больше не использует напрямую).
- Два расхождения в присланной таблице (Risk Assessment: 115+75=190≠200 из GMG Academy;
  Large Vessel Handling: 185+35=220≠225) — заказчик подтвердил, что колонка GMG Academy
  авторитетна, margin пересчитан от неё (85 и 40 соответственно, а не числа из колонки Margin).
- Уточнено и подтверждено заказчиком: «ECDIS Refreshing» остаётся отдельным основным курсом
  (не переименовывается, не сливается с «Passage Planning with ECDIS»), «LICOS (Oil Tanker)»/
  «LICOS (Chemical Tanker)» сохраняют формат «название (судно в скобках)».
  Соответствие таблицы заказчика существующим slug'ам сопоставлено вручную по смыслу
  (например «Right Ship Inspection» ≠ «Tank Inspection» — это два разных существующих курса,
  цена из таблицы под «Tank Inspection» относится именно к `tank-inspection`, не к
  `right-ship-inspection`; «Purifier / Compressor / Auxiliary Machinery» — заказчик подтвердил,
  что единственная строка с ценой $625/$625/$125 в этой теме относится к этому курсу, а не к
  отдельному «High Pressure Air Compressor & Air Cylinder Operation» — тот получил цену
  отдельно во второй порции, см. ниже). Список из 36 обновлённых slug'ов — в
  `courses/fixtures/courses.json` и в скрипте, использованном для применения (не сохранён
  отдельным файлом, только в истории сессии).

**Прайсинг курсов — вторая порция от заказчика (2026-08-25).** Второй скриншот (те же
MMTC/GMG Academy колонки, без заголовков — подтверждено заказчиком: "первая цифра MMTC,
вторая цена на сайте, разница — маржа") покрыл ещё 14 из 17 оставшихся без цены курсов:
`combating-oil-spills-petroleum-product-response`, `high-pressure-air-compressor-air-cylinder-operation`,
`dual-fuel-marine-engine-operation-systems`, `sts-ship-to-ship-transfer-operations`,
`engine-room-management-simulator`, `maritime-cyber-security`, `media-response-crisis-communication`,
`cross-cultural-interpersonal-skills`, `hatch-cover-inspection-maintenance`,
`stress-management-at-sea`, `human-factors-management`, `effective-communication-onboard`,
`operation-of-crew-manning-agency`, `fatigue-awareness-management`. Сопоставление названий
со slug'ами — по смыслу (скриншот с опечатками вида "Duel Fuel"/"Engine roome Managent"),
не подтверждалось заказчиком построчно, в отличие от первой порции. Применено тем же
способом (`training_center_price_usd`/`price_usd`/`commission_percent` пересчитан).

**Итог на 2026-08-25: 50 из 53 курсов имеют цену.** Без цены остаются только 3: `first-aid-for-non-medical-staff-heartsaver-cpr-aed-emergency-cardiovascular-care`,
`passage-planning-with-ecdis`, `shipboard-security` — не покрыты ни одной из присланных
таблиц, ждут отдельного уточнения. `train-the-trainer` сохраняет цену из первой порции
($400 MMTC / $500 GMG Academy) — заказчик написал "уточню" по этому курсу отдельно
(2026-08-24), уточнение ещё не пришло, cо второй порцией не пересекается.

---

## Открыто — решить по ходу, не придумывать самостоятельно

- Точный список языков сайта (английский базовый, остальные — уточнить у заказчика).
- WhatsApp Business API — реализация после верификации бизнеса в Meta.
- Формат Excel-экспорта — согласовать с бухгалтерией заказчика перед реализацией.
- Политика хранения и удаления персональных данных (data retention period) — юридический вопрос, нужен текст от заказчика.
- Конкретные сроки и условия возврата — текст от заказчика для публичной страницы (макет называет «до 3 рабочих дней», как и текущий текст CLAUDE.md — совпадает).
- Чат-бот на сайте (FAQ) — отдельная задача, не включена в текущий скоуп; в `ТЗ для IT.docx` упомянута идея бота "по матрице" вопрос-ответ — деталей пока нет.
- Антифрод-механизм у Fondy (аналог Stripe Radar из старого черновика ТЗ) — уточнить у Fondy, какая защита включена по умолчанию и нужен ли доп. код.
- Требования курса и описание (`description`, `requirements`) в `Course_Description.docx` — не разобран в этой сессии, разобрать при наполнении каталога.
- Формат курса (online / очно-заочно / self-paced) — в макетах есть как отдельный атрибут карточки, в текущей модели `Course` нет явного поля под это (только `duration` строкой) — уточнить, нужно ли отдельное поле.
- **`Course.level`/`category`/`topic`/`instructor_name`/`instructor_bio` заполнены вручную «на глаз» для всех 53 курсов** (см. «Раунд 2» в разделе «Вёрстка» выше) — не подтверждено заказчиком per-course. Сверить и поправить в admin, особенно `level` (Beginner/Intermediate/Advanced) и `topic` — это влияет на то, в какой вкладке/фильтре кандидат находит курс.
- **«Author Courses» реализовано (app `author_courses`, см. «Вёрстка» выше), но данные — demo, не от заказчика.** Все 12 `AuthorCourse` + 8 `CareerPathProgram` в фикстуре скопированы/по аналогии с `author.jpg`, включая 6 engineer-курсов, которых в макете вообще нет (симметричный набор для второй вкладки). Уточнить у заказчика реальные курсы/цены/консультационные услуги для этого каталога, заменить фикстуру.
- **Contact-форма (`pages/contact_us.html`) — только вёрстка, не отправляет письма.** Реальная отправка (email/сохранение обращения) — предмет `support`/`notifications`, не сделано намеренно на этом этапе.
