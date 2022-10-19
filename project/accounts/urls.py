from django.urls import path, include
from rest_framework.routers import SimpleRouter

from . import api

router = SimpleRouter()
router.register(r'users', api.UserViewsSet, basename='user')

urlpatterns = [
    path('api/accounts/', include(router.urls)),
]
