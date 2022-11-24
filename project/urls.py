from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("config/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("base-layers/", include("mapbox_baselayer.urls")),
    path("api/", include("project.geosource.urls", namespace="geosource")),
    path("", include("project.accounts.urls")),
    path("", include("project.visu.urls")),
    path("", include("project.frontend.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
