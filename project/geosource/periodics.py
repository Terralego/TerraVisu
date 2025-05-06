import logging

from project.geosource.models import Source

logger = logging.getLogger(__name__)


def auto_refresh_source():
    countdown = 0
    for source in Source.objects.exclude(status=Source.Status.PENDING):
        if source.should_refresh():
            logger.info("Schedule refresh for source %s<%s>...", source, source.id)
            # Delay execution by some minutes to avoid struggling
            try:
                source.run_async_method("refresh_data", countdown=countdown, force=True)
                countdown += 60 * 3
            except Exception:
                logger.exception("Failed to refresh source!")
