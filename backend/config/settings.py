"""Django settings for Accrubook.

All environment-specific values come from environment variables (12-factor app).
See `.env.example` at the repository root for the full list.
"""

from pathlib import Path

import dj_database_url

from config.env import env_bool, env_list, env_str

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core -------------------------------------------------------------------

SECRET_KEY = env_str("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    # Local apps
    "core",
    "currencies",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Right after SecurityMiddleware (HTTPS redirect and HSTS still apply) and before
    # everything else, so a static file never touches sessions, CSRF or auth.
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ---------------------------------------------------------------

DATABASES = {
    "default": dj_database_url.parse(
        env_str("DATABASE_URL"),
        conn_max_age=60,
        conn_health_checks=True,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files -----------------------------------------------------------
# The app serves its own static files with WhiteNoise: no web server in front on
# Railway (ADR 0007). collectstatic runs at image build time and writes each file
# under a content-hashed name plus a gzip copy, so browsers can cache it forever.
# With DEBUG=True, Django skips the manifest and runserver works without collectstatic.
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --- HTTPS and security headers ---------------------------------------------
# Secure by default: with the variable unset, every HTTPS protection is on.
# Local development over plain HTTP sets DJANGO_HTTPS_ONLY=false in .env.
https_only = env_bool("DJANGO_HTTPS_ONLY", default=True)

# Railway terminates TLS, forwards only HTTPS traffic and sets
# X-Forwarded-Proto: https (ADR 0007). Never trust the header without that proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if https_only else None
# Railway's edge sets X-Real-IP to the client's address (ADR 0007). Read by
# core.throttling; never trusted without the proxy.
CLIENT_IP_HEADER = "HTTP_X_REAL_IP" if https_only else None
SECURE_SSL_REDIRECT = https_only
SESSION_COOKIE_SECURE = https_only
CSRF_COOKIE_SECURE = https_only
# HSTS: browsers refuse plain HTTP to this host (and its subdomains) for a year.
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365 if https_only else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = https_only

# security.W021 (HSTS preload): joining the browser preload list is a decision
# for the whole accrubook.com domain, made at the apex, not by the API.
SILENCED_SYSTEM_CHECKS = ["security.W021"]


# --- Logging ----------------------------------------------------------------
# Production: one JSON object per line on stdout (Railway marks stderr as error).
# Local development sets DJANGO_LOG_JSON=false for readable text.
log_json = env_bool("DJANGO_LOG_JSON", default=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "core.json_logging.JsonFormatter"},
        "text": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json" if log_json else "text",
        },
    },
    "root": {"handlers": ["stdout"], "level": "INFO"},
    # Drop Django's own console handler (stderr, DEBUG only) so nothing is logged
    # twice; its records propagate to the root handler above.
    "loggers": {"django": {"handlers": [], "level": "INFO"}},
}

# --- Cache ------------------------------------------------------------------
# In memory, per gunicorn worker: throttle counters are approximate (one counter
# per worker) and reset on every deploy. A shared cache is revisited in Slice 1.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# --- Django REST Framework (DRF) --------------------------------------------------

REST_FRAMEWORK = {
    # Secure by default: every endpoint requires an authenticated user
    # unless the view explicitly opts out (e.g. permission_classes = [AllowAny]).
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # No authentication backends yet; JWT is added in Slice 1.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    # JSON in, JSON out. No browsable API: Swagger UI covers interactive docs.
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # Paginate every list from day one; adding it later is a breaking change.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Every API error uses RFC 9457 Problem Details (see core/errors.py).
    "EXCEPTION_HANDLER": "core.errors.problem_details_exception_handler",
    # Coarse abuse protection per client IP; approximate, see CACHES.
    "DEFAULT_THROTTLE_CLASSES": ["core.throttling.ClientIPAnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/minute"},
}


swagger_ui_dist = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.35.1"

SPECTACULAR_SETTINGS = {
    "TITLE": "Accrubook API",
    "DESCRIPTION": "Finance operations API for professional services firms.",
    "VERSION": "1.0.0",
    # Don't list the /api/schema/ endpoint inside its own schema.
    "SERVE_INCLUDE_SCHEMA": False,
    # Strip the version prefix so tags/operation IDs read "currencies", not "v1".
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    # Pinned instead of @latest, so a CDN release can't change the docs page silently.
    "SWAGGER_UI_DIST": swagger_ui_dist,
    "SWAGGER_UI_FAVICON_HREF": f"{swagger_ui_dist}/favicon-32x32.png",
}

# The schema and Swagger UI are public pages (a full map of the API), so they are
# off unless enabled: local development and staging only (ADR 0007).
API_DOCS_ENABLED = env_bool("DJANGO_API_DOCS_ENABLED", default=False)


# --- CORS -------------------------------------------------------------------
# Browsers block cross-origin calls unless the API allows the caller's origin.
# Secure by default: no origins allowed unless listed in the environment.
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CORS_URLS_REGEX = r"^/api/.*$"
