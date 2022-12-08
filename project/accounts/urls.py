from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import api, views

router = SimpleRouter()
router.register(r"users", api.UserViewsSet, basename="user")

urlpatterns = [
    path("login/", views.LoginDispatcher.as_view(), name="login_dispatcher"),
    path("", include(router.urls)),
]
