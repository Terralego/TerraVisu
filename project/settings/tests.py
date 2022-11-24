from . import *  # noqa

CELERY_TASK_ALWAYS_EAGER = True

INSTALLED_APPS += ("project.geosource.tests.app",)  # NOQA
