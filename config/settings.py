"""
Django settings for config project.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    "modeltranslation",  # must precede django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "auditlog",
    "courses",
    "applications",
    "payments",
    "notifications",
    "pages",
    "author_courses",
    "refunds",
    "support",
    "legal",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# Managed via DATABASE_URL env var. Defaults to PostgreSQL per project stack;
# override in .env (e.g. sqlite:///db.sqlite3) for local dev without a Postgres server.

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/kyrsi",
    )
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# Site languages: TBD with client (see CLAUDE.md "Открыто"). English is the base language.

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("ru", "Русский"),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("en", "ru")

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static / media files

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Celery — фоновые задачи (генерация PDF + уведомления через 15 мин после оплаты)

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
# В тестах/локально без Redis задачи выполняются синхронно, если явно включить.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)


# Fondy — эквайринг + сплит платежей (см. CLAUDE.md "Платежи")
# Реальные merchant_id/secret_key выдаются Fondy после регистрации и KYB —
# до этого момента поля пустые, интеграция работает только в паре с моком в тестах.

FONDY_MERCHANT_ID = env("FONDY_MERCHANT_ID", default="")
FONDY_SECRET_KEY = env("FONDY_SECRET_KEY", default="")
# receiver_id партнёра (наша компания) — единственная запись, в отличие от TrainingCenter
# не смоделирована отдельной сущностью (см. CLAUDE.md "Модель данных" — Partner там нет).
FONDY_PARTNER_RECEIVER_ID = env("FONDY_PARTNER_RECEIVER_ID", default="")


# Email / уведомления

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@kyrsi.example")
PARTNER_NOTIFICATION_EMAIL = env("PARTNER_NOTIFICATION_EMAIL", default="partner@kyrsi.example")
ACCOUNTING_EMAIL = env("ACCOUNTING_EMAIL", default="accounting@kyrsi.example")

# Telegram — исходящее уведомление партнёру о новой оплате. Полноценный бот
# (интерактивные команды, абстракция под WhatsApp) — app notifications, шаг 4.
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", default="")


# Security — see CLAUDE.md "Безопасность и соответствие стандартам". SSL/HTTPS
# is provided by the hosting platform (Let's Encrypt, per CLAUDE.md "Стек"), so
# these only take effect once the app actually sits behind HTTPS — gated on
# DEBUG so local/dev runs (plain HTTP) are unaffected. CSRF_TRUSTED_ORIGINS is
# empty by default — set it to the real domain(s) via .env once assigned.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    X_FRAME_OPTIONS = "DENY"
