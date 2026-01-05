from django.urls import path

from .views import FeatureSheetAPIView

urlpatterns = [
    path("api/feature_sheet", FeatureSheetAPIView.as_view(), name="feature-sheet"),
]