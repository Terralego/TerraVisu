import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import SimpleRouter

from project.accounts.api import FunctionalPermissionViewSet, GroupViewSet, UserViewsSet
from project.admin import config_site
from project.terra_layer.views.extras import BaseLayerViewSet

router = SimpleRouter()

router.register("baselayer", BaseLayerViewSet, basename="baselayer")
router.register(r"user", UserViewsSet, basename="user")
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"permissions", FunctionalPermissionViewSet, basename="permission")

urlpatterns = [
    path("tinymce/", include("tinymce.urls")),
    path("config/clearcache/", include("clearcache.urls")),
    path("config/", config_site.urls),
    path("debug/", admin.site.urls),
    path("oidc/", include("django_auth_oidc.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("base-layers/", include("mapbox_baselayer.urls")),
    path("api/geosource/", include("project.geosource.urls", namespace="geosource")),
    path("api/geolayer/", include("project.terra_layer.urls")),
    path("api/auth/", include("project.accounts.urls")),
    path("api/", include(router.urls)),
    path("", include("project.visu.urls")),
]

if settings.API_SCHEMA:  # pragma: no cover
    urlpatterns += [path("api/schema/", SpectacularAPIView.as_view(), name="schema")]
    if settings.API_SWAGGER:
        urlpatterns += [
            path(
                "api/schema/swagger/",
                SpectacularSwaggerView.as_view(url_name="schema"),
                name="swagger",
            )
        ]
    if settings.API_REDOC:
        urlpatterns += [
            path(
                "api/schema/redoc/",
                SpectacularRedocView.as_view(url_name="schema"),
                name="redoc",
            )
        ]

if "dev" in os.getenv("DJANGO_SETTINGS_MODULE"):  # pragma: no cover
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static("admin/", document_root=settings.ADMIN_ROOT)
    urlpatterns += (path("__debug__/", include("debug_toolbar.urls")),)
