from tempfile import TemporaryDirectory

from . import *  # noqa

CELERY_TASK_ALWAYS_EAGER = True
SECRET_KEY = "secret-key-for-tests-do-not-use-in-production"
INSTALLED_APPS += ("project.geosource.tests.app",)  # NOQA
MEDIA_ROOT = TemporaryDirectory().name

CACHES["default"] = {  # NOQA
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
}

CONSTANCE_BACKEND = "constance.backends.memory.MemoryBackend"
