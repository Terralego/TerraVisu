from constance import config
from django.conf import settings


def custom_settings(request):
    return {
        "OIDC_ENABLED": settings.OIDC_ENABLE_LOGIN,
        "INSTANCE_TITLE": config.INSTANCE_TITLE,
        "INSTANCE_LOGO": config.INSTANCE_LOGO,
        "INSTANCE_FAVICON": config.INSTANCE_FAVICON,
    }
