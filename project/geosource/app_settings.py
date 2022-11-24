from django.conf import settings

# Max time a task can be running until another one can be runned.
# This is to prevent when a task is blocked.
MAX_TASK_RUNTIME = getattr(settings, "GEOSOURCE_MAX_TASK_RUNTIME", 24)
