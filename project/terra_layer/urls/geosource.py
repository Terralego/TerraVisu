from rest_framework import routers

from ..views import GeoSourceModelViewset

router = routers.SimpleRouter()

router.register(r"", GeoSourceModelViewset, basename="geosource")
