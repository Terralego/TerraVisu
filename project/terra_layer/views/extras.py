from geostore.views import FeatureViewSet, LayerGroupViewsSet, LayerViewSet
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from project.terra_layer.models import Report
from project.terra_layer.serializers import ReportSerializer

from ..permissions import ReadOnly
from ..serializers import MapBaseLayerSerializer


class GeostoreLayerViewSet(LayerViewSet):
    permission_classes = (ReadOnly,)


class GeostoreFeatureViewSet(FeatureViewSet):
    permission_classes = (ReadOnly,)


class GeostoreLayerGroupViewsSet(LayerGroupViewsSet):
    permission_classes = (ReadOnly,)


class BaseLayerViewSet(viewsets.ModelViewSet):
    serializer_class = MapBaseLayerSerializer
    queryset = MapBaseLayer.objects.all()

    @action(detail=True)
    def tilejson(self, request, *args, **kwargs):
        """Full tilejson"""
        base_layer = self.get_object()
        return Response(base_layer.tilejson)


class ReportCreateAPIView(generics.CreateAPIView):
    model = Report
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
