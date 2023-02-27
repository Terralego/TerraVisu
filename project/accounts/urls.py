from django.urls import path
from rest_framework_jwt import views as auth_views

from . import views

urlpatterns = [
    path("login/", views.LoginDispatcher.as_view(), name="login_dispatcher"),
    # jwt process
    path("obtain-token/", auth_views.obtain_jwt_token, name="token-obtain"),
    path("verify-token/", auth_views.verify_jwt_token, name="token-verify"),
    path("refresh-token/", auth_views.refresh_jwt_token, name="token-refresh"),
]
