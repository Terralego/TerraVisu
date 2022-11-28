from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import api

router = SimpleRouter()
router.register(r"users", api.UserViewsSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
