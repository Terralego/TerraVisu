import logging

from celery import shared_task, states
from celery.exceptions import Ignore
from constance import config
from django.apps import apps
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import gettext as _

from project.visu.utils import get_logo_url

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

    if config.INSTANCE_EMAIL_SOURCE_REFRESH_RECIPIENTS:
        obj.refresh_from_db()
        mail_level = config.INSTANCE_EMAIL_SOURCE_REFRESH_LEVEL
        if (
            mail_level == "success"
            or (mail_level == "warning" and obj.report.status in (1, 2))
            or (mail_level == "error" and obj.report.status == 1)
        ):
            emails = config.INSTANCE_EMAIL_SOURCE_REFRESH_RECIPIENTS.split(",")
            logo_url = f"{config.INSTANCE_EMAIL_MEDIA_BASE_URL}{get_logo_url()}"
            context = {
                "title": config.INSTANCE_TITLE,
                "obj": obj,
                "logo_url": logo_url,
            }
            txt_template = get_template("emails/source_refresh/email.txt")
            txt_message = txt_template.render(context=context)
            html_template = get_template("emails/source_refresh/email.html")
            html_message = html_template.render(context)
            send_mail(
                _(
                    "%(title)s : Data source %(obj)s refresh ended with state %(success_state)s"
                )
                % {
                    "title": config.INSTANCE_TITLE,
                    "obj": obj,
                    "success_state": obj.report.get_status_display(),
                },
                txt_message,
                config.INSTANCE_EMAIL_FROM,
                recipient_list=emails,
                html_message=html_message,
                fail_silently=True,
            )

    raise Ignore()


@shared_task(bind=True)
def run_auto_refresh_source(*args, **kwargs):
    from project.geosource.periodics import auto_refresh_source

    auto_refresh_source()
