import logging

from django.contrib.auth.models import Group
from django.contrib.gis.geos import GEOSGeometry
from geostore.models import Layer, LayerGroup

logger = logging.getLogger(__name__)


def layer_callback(geosource):

    group_name = geosource.settings.pop("group", "reference")

    defaults = {
        "settings": geosource.settings,
    }

    layer, _ = Layer.objects.get_or_create(name=geosource.slug, defaults=defaults)

    layer_groups = Group.objects.filter(pk__in=geosource.settings.get("groups", []))

    if set(layer.authorized_groups.all()) != set(layer_groups):
        layer.authorized_groups.set(layer_groups)

    if not layer.layer_groups.filter(name=group_name).exists():
        group, _ = LayerGroup.objects.get_or_create(name=group_name)
        group.layers.add(layer)

    return layer


def feature_callback(geosource, layer, identifier, geometry, attributes):
    # Force converting geometry to 4326 projection
    try:
        geom = GEOSGeometry(geometry)
        geom.transform(4326)
        return layer.features.update_or_create(
            identifier=identifier, defaults={"properties": attributes, "geom": geom}
        )[0]
    except (TypeError, ValueError):
        logger.warning(
            f"One record was ignored from source, because of invalid geometry: {attributes}"
        )
        return None


def clear_features(geosource, layer, begin_date):
    return layer.features.filter(updated_at__lt=begin_date).delete()


def delete_layer(geosource):
    geosource.get_layer().features.all().delete()
    return geosource.get_layer().delete()
