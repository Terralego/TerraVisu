from django.conf import settings

from project.visu import settings as visu_settings


def custom_settings(request):
    return {
        "OIDC_ENABLED": settings.OIDC_ENABLE_LOGIN,
        "INSTANCE_TITLE": visu_settings.INSTANCE_TITLE,
        "INSTANCE_LOGO": visu_settings.INSTANCE_LOGO,
    }
