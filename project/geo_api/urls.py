from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"feature", views.FeatureViewSet, basename="geo-api-feature")

urlpatterns = [
    path("<str:layer>/", include(router.urls)),
]