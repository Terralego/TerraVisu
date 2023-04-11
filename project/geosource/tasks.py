import logging

from celery import shared_task, states
from celery.exceptions import Ignore
from django.apps import apps

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
    if instance and hasattr(instance, "report"):
        text = ""
        for key, value in state["meta"].items():
            text += f"{key}: {value},"
        instance.report["lines"] = text
        instance.save(update_fields=["report"])


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
        if obj and hasattr(obj, "report"):
            text = ""
            for key, value in state.items():
                text += f"{key}: {value},"
            obj.report["lines"] = text
            obj.save(update_fields=["report"])

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
