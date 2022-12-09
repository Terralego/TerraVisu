from django.conf import settings


def custom_settings(request):
    return {"OIDC_ENABLED": settings.OIDC_ENABLE_LOGIN}
