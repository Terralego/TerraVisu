from django.urls import path

from . import views

urlpatterns = [
    path("communes/", views.communes),
]
