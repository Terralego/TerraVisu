from django.urls import include, path
from rest_framework import routers

from ..views import (
    LayerViewset,
    ReportCreateAPIView,
    ReportListAPIView,
    SceneTreeAPIView,
    SceneViewset,
)
from ..views.extras import DeclarationConfigDetailAPIView, DeclarationCreateAPIView
from ..views.layers import (
    SceneCustomStyleLayerAPIView,
    SceneCustomStyleSourceAPIView,
    SceneLayerDetailAPIView,
)
from .geostore import urlpatterns as geostore_patterns

router = routers.SimpleRouter()

router.register(r"scene", SceneViewset, basename="scene")
router.register(r"", LayerViewset, basename="layer")

# Extras viewsets

urlpatterns = [
    path("view/<str:slug>/", SceneTreeAPIView.as_view(), name="layerview"),
    path(
        "view/<slug:slug>/layersTree/layers/<int:layer_id>",
        SceneLayerDetailAPIView.as_view(),
        name="scene-layer-detail",
    ),
    path(
        "view/<slug:slug>/customStyle/source/<int:pk>",
        SceneCustomStyleSourceAPIView.as_view(),
        name="scene-customstyle-source",
    ),
    path(
        "view/<slug:slug>/customStyle/layer/<int:layer_id>",
        SceneCustomStyleLayerAPIView.as_view(),
        name="scene-customstyle-layer",
    ),
    # Extra urls from third part modules
    path("geostore/", include(geostore_patterns)),
    path("report/", ReportCreateAPIView.as_view(), name="report-create-view"),
    path("reports/", ReportListAPIView.as_view(), name="report-list-view"),
    path(
        "declaration/config/",
        DeclarationConfigDetailAPIView.as_view(),
        name="declaration-config-detail-view",
    ),
    path(
        "declaration/",
        DeclarationCreateAPIView.as_view(),
        name="declaration-create-view",
    ),
    path("", include(router.urls)),
]
