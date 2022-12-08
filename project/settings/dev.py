from . import *  # NOQA

DEBUG = True
INSTALLED_APPS += ("debug_toolbar",)  # NOQA

MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)  # NOQA

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda x: True,
}
