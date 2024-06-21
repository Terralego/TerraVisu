from constance import config
from django.core.files.storage import default_storage


def get_logo_url(request=None):
    if config.INSTANCE_LOGO.startswith("/"):
        LOGO_URL = config.INSTANCE_LOGO
    else:
        LOGO_URL = default_storage.url(config.INSTANCE_LOGO)

    return request.build_absolute_uri(LOGO_URL) if request else f"/{LOGO_URL}"


def get_emails_recipients():
    return config.INSTANCE_EMAIL_SOURCE_REFRESH_RECIPIENTS.split(",")
