import os

from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery("project")


BROKER_URL = f'redis://{os.getenv("REDIS_HOST", "redis")}:{os.getenv("REDIS_PORT", "6379")}/{os.getenv("REDIS_DB", "0")}'

app.conf.update(
    timezone=settings.TIME_ZONE,
    accept_content=["json"],
    broker_url=BROKER_URL,
    task_serializer="json",
    result_serializer="json",
    result_expires=5,
    result_backend="django-db",
    cache_backend="django-cache",
    beat_scheduler="django_celery_beat.schedulers:DatabaseScheduler",
    result_extended=True,
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
)


app.autodiscover_tasks()
