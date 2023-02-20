from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_jwt import views as auth_views

from . import api, views

router = SimpleRouter()
router.register(r"users", api.UserViewsSet, basename="user")

urlpatterns = [
    path("login/", views.LoginDispatcher.as_view(), name="login_dispatcher"),
    # jwt process
    path("auth/obtain-token/", auth_views.obtain_jwt_token, name="token-obtain"),
    path("auth/verify-token/", auth_views.verify_jwt_token, name="token-verify"),
    path("auth/refresh-token/", auth_views.refresh_jwt_token, name="token-refresh"),
    path("", include(router.urls)),
]
