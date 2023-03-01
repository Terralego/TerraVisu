from constance import config
from django.conf import settings
from django.core.files.storage import default_storage


def custom_settings(request):
    return {
        "OIDC_ENABLED": settings.OIDC_ENABLE_LOGIN,
        "INSTANCE_TITLE": config.INSTANCE_TITLE,
        "INSTANCE_LOGO": config.INSTANCE_LOGO
        if config.INSTANCE_LOGO.startswith("/")
        else default_storage.url(config.INSTANCE_LOGO),
        "INSTANCE_FAVICON": config.INSTANCE_FAVISON
        if config.INSTANCE_FAVISON.startswith("/")
        else default_storage.url(config.INSTANCE_FAVISON),
    }
