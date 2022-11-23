from django.urls import path

from . import api

urlpatterns = [
    path("api/settings/", api.SettingsView.as_view(), name="settings"),
]
