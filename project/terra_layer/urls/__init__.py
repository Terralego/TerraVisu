from django.urls import include, path
from rest_framework import routers

from ..views import LayerViewset, SceneTreeAPIView, SceneViewset
from .geostore import urlpatterns as geostore_patterns

router = routers.SimpleRouter()

router.register(r"scene", SceneViewset, basename="scene")
router.register(r"", LayerViewset, basename="layer")

# Extras viewsets

urlpatterns = [
    path("view/<str:slug>/", SceneTreeAPIView.as_view(), name="layerview"),
    # Extra urls from third part modules
    path("geostore/", include(geostore_patterns)),
    path("", include(router.urls)),
]
