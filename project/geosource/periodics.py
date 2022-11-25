import logging

from project.geosource.models import Source

logger = logging.getLogger(__name__)


def auto_refresh_source():
    countdown = 0
    for source in Source.objects.all():
        logger.info(f"Is refresh for {source}<{source.id}> needed?")
        if source.should_refresh():
            logger.info(f"Schedule refresh for source {source}<{source.id}>...")
            # Delay execution by some minutes to avoid struggling
            try:
                source.run_async_method("refresh_data", countdown=countdown, force=True)
                countdown += 60 * 3
            except Exception:
                logger.exception("Failed to refresh source!")
