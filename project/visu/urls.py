from django.urls import path

from . import api

urlpatterns = [
    path(
        "api/settings/frontend",
        api.SettingsFrontendView.as_view(),
        name="settings-frontend",
    ),
    path("api/settings/", api.SettingsAdminView.as_view(), name="settings"),
    path("env.json", api.EnvFrontendView.as_view(), name="env-front"),
]
