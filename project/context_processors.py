from project.accounts import settings as account_settings


def custom_settings(request):
    return {"OIDC_ENABLED": account_settings.OIDC_ENABLE_LOGIN}
