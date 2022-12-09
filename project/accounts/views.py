from django.conf import settings
from django.urls import reverse
from django.views.generic import RedirectView


class LoginDispatcher(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if settings.OIDC_ENABLE_LOGIN and settings.OIDC_DISABLE_INTERNAL_LOGIN:
            return "/oidc/"
        else:
            return reverse("login")
