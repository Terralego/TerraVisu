from django.urls import reverse
from django.views.generic import RedirectView

from . import settings as account_settings


class LoginDispatcher(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if (
            account_settings.OIDC_ENABLE_LOGIN
            and account_settings.OIDC_DISABLE_INTERNAL_LOGIN
        ):
            return "/oidc/"
        else:
            return reverse("login")
