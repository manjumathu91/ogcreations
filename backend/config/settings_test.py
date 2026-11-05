"""Test settings: SQLite in-memory, local-memory email, no SSL redirects. NOT for production."""
from .settings import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "test-secret-key"
ALLOWED_HOSTS = ["testserver", "localhost"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
import tempfile  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp(prefix="og_test_media_")
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
AI_ENABLED = True
GROQ_API_KEY = ""
GROQ_MODEL = ""
DEFAULT_FROM_EMAIL = "studio@example.com"
ADMIN_NOTIFY_EMAIL = "admin@example.com"
DEFAULT_THROTTLE = {}
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"leads": "1000/hour", "ai_public": "1000/minute", "ai_admin": "1000/minute"}}
