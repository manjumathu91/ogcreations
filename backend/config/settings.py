"""
OG Creations - Django settings.

All secrets and environment-specific values come from environment variables
(see .env.example). Nothing sensitive is hardcoded here.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# --------------------------------------------------------------------------- helpers
def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------- core
DEBUG = env_bool("DEBUG", False)

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "insecure-dev-key-change-me-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("SECRET_KEY environment variable is required when DEBUG=False.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
if env("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(env("RENDER_EXTERNAL_HOSTNAME"))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "apps.core",
    "apps.accounts",
    "apps.dashboard",
    "apps.site_settings",
    "apps.navigation",
    "apps.pages",
    "apps.services",
    "apps.portfolio",
    "apps.gallery",
    "apps.projects",
    "apps.leads",
    "apps.communications",
    "apps.media_library",
    "apps.ai_assistant",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.dashboard.context_processors.dashboard",
            ],
        },
    },
]

# --------------------------------------------------------------------------- database
# MySQL is the primary database. SQLite is ONLY for optional local development (DB_ENGINE=sqlite).
if env("DB_ENGINE", "mysql").lower() == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    _db_options = {"charset": "utf8mb4"}
    if env("DB_SSL_CA"):
        _db_options["ssl"] = {"ca": env("DB_SSL_CA")}
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME", "og_creations"),
            "USER": env("DB_USER", "root"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST", "127.0.0.1"),
            "PORT": env("DB_PORT", "3306"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),

           "OPTIONS": {
    **_db_options,
    "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
},
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- auth
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"
SESSION_COOKIE_AGE = env_int("SESSION_COOKIE_AGE", 60 * 60 * 12)  # 12 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# --------------------------------------------------------------------------- i18n
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- static & media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", str(BASE_DIR / "media")))
# Serving uploads from Django is fine for small sites / demos. For heavy production use
# put MEDIA_ROOT on persistent storage behind nginx or use S3-compatible storage.
SERVE_MEDIA = env_bool("SERVE_MEDIA", DEBUG)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

MAX_IMAGE_UPLOAD_MB = env_int("MAX_IMAGE_UPLOAD_MB", 5)
MAX_VIDEO_UPLOAD_MB = env_int("MAX_VIDEO_UPLOAD_MB", 50)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# --------------------------------------------------------------------------- REST framework
REST_FRAMEWORK = {
    # Secure by default: admin endpoints need a logged-in staff session.
    # Public endpoints explicitly override with AllowAny + no authentication.
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
    "DEFAULT_RENDERER_CLASSES": (
        ["rest_framework.renderers.JSONRenderer", "rest_framework.renderers.BrowsableAPIRenderer"]
        if DEBUG
        else ["rest_framework.renderers.JSONRenderer"]
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_THROTTLE_RATES": {
        "leads": env("THROTTLE_LEADS", "10/hour"),
        "ai_public": env("THROTTLE_AI_PUBLIC", "30/minute"),
        "ai_admin": env("THROTTLE_AI_ADMIN", "60/minute"),
    },
}

# --------------------------------------------------------------------------- CORS / CSRF
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://localhost:8080",
)
CORS_URLS_REGEX = r"^/api/(?!admin/).*$"  # public API only; admin API is same-origin
CORS_ALLOW_CREDENTIALS = False
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
FRONTEND_URL = env("FRONTEND_URL", "")  # optional: shown as "Visit website" in the dashboard

# --------------------------------------------------------------------------- email (SMTP)
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@example.com")
ADMIN_NOTIFY_EMAIL = env("ADMIN_NOTIFY_EMAIL")  # falls back to the email in Site Settings
EMAIL_BACKEND = env("EMAIL_BACKEND") or (
    "django.core.mail.backends.console.EmailBackend"
    if (DEBUG and not EMAIL_HOST)
    else "django.core.mail.backends.smtp.EmailBackend"
)

# --------------------------------------------------------------------------- AI (Groq)
AI_ENABLED = env_bool("AI_ENABLED", True)
GROQ_API_KEY = env("GROQ_API_KEY")
GROQ_MODEL = env("GROQ_MODEL")
GROQ_API_URL = env("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
AI_REQUEST_TIMEOUT = env_int("AI_REQUEST_TIMEOUT", 30)

# --------------------------------------------------------------------------- production security
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "[{levelname}] {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
