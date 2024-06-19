from . import *  # NOQA

DEBUG = True
SECRET_KEY = "secret-key-for-dev-do-not-use-in-production"
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS += ("debug_toolbar",)  # NOQA

MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)  # NOQA

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda x: True,
}

# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = VAR_DIR / "mails"  # NOQA
