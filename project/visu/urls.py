from django.urls import path

from . import api

urlpatterns = [
    path(
        "api/settings/frontend",
        api.SettingsFrontendView.as_view(),
        name="settings-frontend",
    ),
    path("api/settings/", api.SettingsAdminView.as_view(), name="settings-admin"),
    path("api/sprites", api.SpriteDataAPIView.as_view(), name="sprites"),
    path("api/feature_sheet", api.FeatureSheetAPIView.as_view(), name="feature-sheet"),
    path("api/sprites.json", api.SpriteDataAPIView.as_view(), name="sprites-json"),
    path("env.json", api.EnvFrontendView.as_view(), name="env-front"),
]
