from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import RedirectView
from django.contrib.auth import login
from project.accounts.models import PermanentAccessToken


class LoginDispatcher(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if settings.OIDC_ENABLE_LOGIN and settings.OIDC_DISABLE_INTERNAL_LOGIN:
            return "/oidc/"
        else:
            return reverse("login")


class LoginWithToken(View):
    def get(self, *args, **kwargs):
        token = self.request.GET.get("token")
        user = get_object_or_404(PermanentAccessToken, token=token).user
        login(self.request, user=user)
        self.request.user = user
        return redirect(self.request.GET.get("url", "/"))
