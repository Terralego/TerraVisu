from . import *  # NOQA

DEBUG = True
SECRET_KEY = "secret-key-for-dev-do-not-use-in-production"
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS += ("debug_toolbar",)  # NOQA

MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)  # NOQA

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda x: True,
}

API_SCHEMA = True
API_SWAGGER = True
API_REDOC = True
