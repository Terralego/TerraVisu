from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"feature", views.FeatureViewSet, basename="geo-api-feature")

urlpatterns = [
    # <str:layer> = slug ou ID (communes-simplifiees ou 14 par ex)
    path("<str:layer>/", include(router.urls)),
]