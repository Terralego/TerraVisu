from geostore.views import FeatureViewSet, LayerGroupViewsSet, LayerViewSet
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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
