import logging

from celery import shared_task
from constance import config
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import gettext as _

from project.geosource.models import Source
from project.visu.utils import get_emails_recipients, get_logo_url

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def periodic_source_refresh_report(*args, **kwargs):
    if config.INSTANCE_EMAIL_SOURCE_TYPE != "periodic":
        logger.debug("Periodic source refresh report: report is disabled")
        return True
    mail_level = config.INSTANCE_EMAIL_SOURCE_REFRESH_LEVEL
    last_report = config.INSTANCE_EMAIL_SOURCE_LAST_PERIODIC

    level_exclude = {
        "success": [3],
        "warning": [0, 3],
        "error": [0, 2, 3],
    }
    impacted_sources = (
        Source.objects.filter(
            last_refresh__isnull=False,
            last_refresh__gte=last_report,
            report__isnull=False,
        )
        .select_related("report")
        .order_by("-last_refresh")
    )
    impacted_sources = impacted_sources.exclude(
        report__status__in=level_exclude.get(mail_level, [])
    )
    impacted_sources_success = impacted_sources.filter(
        report__status=0,
    )
    impacted_sources_warning = impacted_sources.filter(
        report__status=2,
    )
    impacted_sources_error = impacted_sources.filter(
        report__status=1,
    )

    email_recipients = get_emails_recipients()
    logger.debug(
        "Periodic source refresh report: %s sources(s), send to %s",
        impacted_sources.count(),
        email_recipients,
    )
    if impacted_sources and email_recipients:
        logo_url = f"{config.INSTANCE_EMAIL_MEDIA_BASE_URL}{get_logo_url()}"
        context = {
            "title": config.INSTANCE_TITLE,
            "sources_count": impacted_sources.count(),
            "sources_success": impacted_sources_success,
            "sources_warning": impacted_sources_warning,
            "sources_error": impacted_sources_error,
            "logo_url": logo_url,
        }
        txt_template = get_template("emails/sources_periodic_report/email.txt")
        txt_message = txt_template.render(context=context)
        html_template = get_template("emails/sources_periodic_report/email.html")
        html_message = html_template.render(context)
        send_mail(
            _("%(title)s: Periodic data source refresh report")
            % {
                "title": config.INSTANCE_TITLE,
            },
            txt_message,
            None,
            recipient_list=email_recipients,
            html_message=html_message,
            fail_silently=True,
        )
        logger.debug("Periodic source refresh report: mail sent")
        config.INSTANCE_EMAIL_SOURCE_LAST_PERIODIC = timezone.now()
    else:
        logger.debug("Periodic source refresh report: mail not sent")
    return True
