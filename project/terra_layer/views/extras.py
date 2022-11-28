from geostore.views import FeatureViewSet, LayerGroupViewsSet, LayerViewSet

from project.geosource.views import SourceModelViewset

from ..permissions import ReadOnly, SourcePermission


class GeoSourceModelViewset(SourceModelViewset):
    permission_classes = (SourcePermission,)


class GeostoreLayerViewSet(LayerViewSet):
    permission_classes = (ReadOnly,)


class GeostoreFeatureViewSet(FeatureViewSet):
    permission_classes = (ReadOnly,)


class GeostoreLayerGroupViewsSet(LayerGroupViewsSet):
    permission_classes = (ReadOnly,)
