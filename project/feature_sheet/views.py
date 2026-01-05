from rest_framework import permissions
from rest_framework.generics import ListAPIView

from .models import FeatureSheet
from .serializers import FeatureSheetSerializer


class FeatureSheetAPIView(ListAPIView):
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = FeatureSheetSerializer
    queryset = FeatureSheet.objects.all()
