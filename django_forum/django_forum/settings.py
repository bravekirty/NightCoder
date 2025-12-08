import pathlib
import sys

import decouple
import django.urls

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

SECRET_KEY = decouple.config("DJANGO_SECRET_KEY", default="FAKE-SECRET-KEY")
DEBUG = decouple.config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = decouple.config("DJANGO_ALLOWED_HOSTS", default="*", cast=lambda v: v.split(","))

IS_TESTING = "test" in sys.argv

INSTALLED_APPS = [
    "users.apps.UsersConfig",  # Before django.contrib.auth
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
    "forum.apps.ForumConfig",
    "reviews.apps.ReviewsConfig",
    "votes.apps.VotesConfig",
    "home.apps.HomeConfig",
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
]

ROOT_URLCONF = "django_forum.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.community_stats",
            ],
        },
    },
]

WSGI_APPLICATION = "django_forum.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": decouple.config("DB_NAME"),
        "USER": decouple.config("DB_USER"),
        "PASSWORD": decouple.config("DB_PASSWORD"),
        "HOST": decouple.config("DB_HOST"),
        "PORT": decouple.config("DB_PORT"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("ru", "Русский"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static_dev",
]

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


if DEBUG or IS_TESTING:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]
    INTERNAL_IPS = ["*"]
else:
    CSRF_TRUSTED_ORIGINS = decouple.config(
        "DJANGO_CSRF_TRUSTED_ORIGINS", default="http://*", cast=lambda v: v.split(",")
    )
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    "users.utils.backends.EmailAuthBackend",
]

LOGIN_URL = django.urls.reverse_lazy("users:login")
LOGOUT_REDIRECT_URL = django.urls.reverse_lazy("users:login")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "django_tests.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "users.tests": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "users": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
