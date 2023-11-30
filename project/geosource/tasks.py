import logging

from celery import shared_task, states
from celery.exceptions import Ignore
from django.apps import apps
from django.utils import timezone

logger = logging.getLogger(__name__)


def set_failure_state(task, method, message, instance=None):
    # Failure messaging needs to be formed as expected by celery API
    logger.warning(message)
    state = {
        "state": states.FAILURE,
        "meta": {
            "method": method,
            "exc_type": Exception.__name__,
            "exc_message": [message],
        },
    }
    task.update_state(**state)
    if instance and hasattr(instance, "report") and instance.report is not None:
        text = ""
        for key, value in state["meta"].items():
            text += f"{key}: {value},"
        if not instance.report.status:
            instance.report.status = instance.report.Status.ERROR
        instance.report.message = text
        if not instance.report.started:
            instance.report.started = timezone.now()
        instance.report.ended = timezone.now()
        instance.report.save(update_fields=["status", "started", "ended", "message"])


@shared_task(bind=True)
def run_model_object_method(self, app, model, pk, method, success_state=states.SUCCESS):
    self.update_state(state=states.STARTED)

    Model = apps.get_app_config(app).get_model(model)

    try:
        obj = Model.objects.get(pk=pk)
        # raise Exception("not okkkkkkk")
        logger.info(f"Call method {method} on {obj}")
        state = {"action": method, **getattr(obj, method)()}
        logger.info(f"Method {method} on {obj} ended")

        self.update_state(state=success_state, meta=state)

    except Model.DoesNotExist:
        set_failure_state(
            self, method, f"{Model}'s object with pk {pk} doesn't exist", None
        )

    except AttributeError as e:
        set_failure_state(
            self, method, f"{method} doesn't exist for object {obj}: {e}", obj
        )
        logger.error(e, exc_info=True)

    except Exception as e:
        if hasattr(e, "message"):
            message = e.message
        else:
            message = f"{e}"
        set_failure_state(self, method, message, obj)
        logger.error(e, exc_info=True)

    raise Ignore()


@shared_task(bind=True)
def run_auto_refresh_source(*args, **kwargs):
    from project.geosource.periodics import auto_refresh_source

    auto_refresh_source()
