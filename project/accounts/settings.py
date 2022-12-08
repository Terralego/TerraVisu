from django.conf import settings
from django.db import models
from siteprefs.toolbox import preferences

OIDC_ENABLE_LOGIN = getattr(settings, "OIDC_ENABLE_LOGIN", False)
OIDC_DISABLE_INTERNAL_LOGIN = getattr(settings, "OIDC_DISABLE_INTERNAL_LOGIN", False)

with preferences() as prefs:
    prefs(
        prefs.group(
            "OIDC",
            (
                prefs.one(
                    OIDC_ENABLE_LOGIN,
                    field=models.BooleanField(),
                    verbose_name="Enable login",
                    help_text="Allow OIDC login. Set environmeent variables to configure OIDC.",
                    static=False,
                ),
                prefs.one(
                    OIDC_DISABLE_INTERNAL_LOGIN,
                    field=models.BooleanField(),
                    verbose_name="Disable internal login",
                    help_text="Disable internal login. Only OIDC login is allowed and login redirect to OIDC.",
                    static=False,
                ),
            ),
            static=False,
        ),
    )
