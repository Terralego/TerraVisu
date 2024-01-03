import logging
import tempfile
from copy import deepcopy
from urllib.parse import unquote

from constance import config
from django.core.cache import cache
from django.core.management import call_command, get_commands
from django.db.models import Prefetch, Q
from django.http import Http404, QueryDict
from django.urls import reverse
from django.utils.functional import cached_property
from geostore.tokens import tiles_token_generator
from mapbox_baselayer.models import MapBaseLayer
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from project.geosource.models import FieldTypes, WMTSSource

from ..filters import LayerFilterSet, SceneFilterSet
from ..models import CustomStyle, FilterField, Layer, LayerGroup, Scene, StyleImage
from ..permissions import LayerPermission, ScenePermission
from ..serializers import (
    LayerDetailSerializer,
    LayerListSerializer,
    SceneDetailSerializer,
    SceneListSerializer,
    StyleImageSerializer,
)
from ..sources_serializers import SourceSerializer
from ..utils import dict_merge, get_scene_tree_cache_key

# Map source field data_type to format_type
TYPE_MAP = {a: b.name.lower() for a, b in dict(FieldTypes.choices()).items()}

logger = logging.getLogger(__name__)


class SceneViewset(ModelViewSet):
    queryset = Scene.objects.all()
    permission_classes = (ScenePermission,)
    filterset_class = SceneFilterSet

    def get_serializer_class(self):
        if self.action in ["retrieve", "update", "create", "partial_update"]:
            return SceneDetailSerializer
        return SceneListSerializer

    def check_layer_status(self, view_id, current_node):
        """
        Check all layers in tree to valide existence and scene ownership.
        Recursive process.

        :param current_node: Current node from the tree
        """

        for item in current_node:
            if "geolayer" in item:
                try:
                    # Is layer deleted ?
                    layer = Layer.objects.get(pk=item["geolayer"])
                except Layer.DoesNotExist:
                    raise ValidationError(
                        f"Layer {item['geolayer']} doesn't exists anymore"
                    )

                # Is layer owned by another scene ?
                if layer.group and layer.group.view_id != view_id:
                    raise ValidationError(
                        f"Layer {item['geolayer']} can't be stolen from another scene"
                    )
            else:
                # And we start with the new node
                self.check_layer_status(view_id, item["children"])

    def handle_import_file(self, scene_name):
        if "load_xls" in get_commands() and "file" in self.request.FILES:
            # Handle imported file
            with tempfile.NamedTemporaryFile(suffix=".xls") as xls_file:
                for chunk in self.request.FILES["file"]:
                    xls_file.write(chunk)

                xls_file.seek(0)

                call_command("load_xls", scene_name=scene_name, file=xls_file.name)

    def perform_update(self, serializer):
        if serializer.is_valid():
            self.check_layer_status(
                serializer.instance.id, serializer.validated_data.get("tree", [])
            )
            serializer.save()
        self.handle_import_file(serializer.instance.name)

    def perform_create(self, serializer):
        if serializer.is_valid():
            self.check_layer_status(None, serializer.validated_data.get("tree", []))
            serializer.save()

        self.handle_import_file(serializer.instance.name)


class LayerViewset(ModelViewSet):
    queryset = Layer.objects.all()
    ordering_fields = (
        "name",
        "source__name",
        "group__view__name",
        "active_by_default",
        "order",
        "in_tree",
    )
    filterset_class = LayerFilterSet
    permission_classes = (LayerPermission,)
    search_fields = ["name", "settings"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "update", "create", "partial_update"]:
            return LayerDetailSerializer
        return LayerListSerializer

    def perform_destroy(self, instance):
        if instance.group:  # Prevent deletion of layer used in any layer tree
            raise ValidationError("Can't delete a layer linked to a scene")
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, *args, **kwargs):
        object = self.get_object()
        clone = object.make_clone()
        return Response(self.get_serializer(clone).data, status=201)


class SceneTreeAPIView(APIView):
    """This view generates the LayersTree used to construct the frontend"""

    permission_classes = ()
    EXTERNAL_SOURCES_CLASSES = [WMTSSource]
    DEFAULT_SOURCE_NAME = "terra"
    DEFAULT_SOURCE_TYPE = "vector"

    prefetch_layers = Prefetch(
        "layers",
        (
            Layer.objects.select_related("source").prefetch_related(
                Prefetch(
                    "fields_filters",
                    FilterField.objects.filter(shown=True).select_related("field"),
                    to_attr="filters_shown",
                ),
                Prefetch(
                    "fields_filters",
                    FilterField.objects.filter(filter_enable=True).select_related(
                        "field"
                    ),
                    to_attr="filters_enabled",
                ),
                "extra_styles__source",
            )
        ),
    )

    scene = None

    def get(self, request, slug=None, format=None):
        update_cache = request.query_params.get("cache") == "false"
        self.scene = get_object_or_404(Scene, slug=slug)
        self.layergroup = self.layers.first().source.get_layer().layer_groups.first()
        self.user_groups = tiles_token_generator.get_groups_intersect(
            self.request.user, self.layergroup
        )
        cache_key = get_scene_tree_cache_key(self.scene, self.user_groups)
        if update_cache:
            response = self.get_response_with_sources()
            cache.set(cache_key, response)
        else:
            response = cache.get_or_set(cache_key, self.get_response_with_sources)
        return Response(response)

    def get_response_with_sources(self):
        """Return a response object containing the full layersTree with updated
        user authentication.
        """

        layer_structure = self.get_layer_structure()

        querystring = QueryDict(mutable=True)

        # When the user is not anonymous, we provide tokens in the URL to authenticated
        # it in the MVT endpoint
        if not self.request.user.is_anonymous:
            querystring.update(
                {
                    "idb64": tiles_token_generator.token_idb64(
                        self.user_groups, self.layergroup
                    ),
                    "token": tiles_token_generator.make_token(
                        self.user_groups, self.layergroup
                    ),
                }
            )

        custom_style_infos = []
        for i, layer in enumerate(self.layers.all()):
            if layer.extra_styles.exists():
                # Layer's extra styles have "sub sources" & "sub layers" we need to handle
                for y, style in enumerate(layer.extra_styles.all()):
                    sub_source = style.source
                    sub_layer = sub_source.get_layer()
                    subl_url = reverse("layer-tilejson", args=(sub_layer.id,))
                    sub_source_id = f"{self.DEFAULT_SOURCE_NAME}_{i}_{y}"
                    custom_style_infos.append((subl_url, sub_source_id))

                    for map_layer in layer_structure["map"]["customStyle"]["layers"]:
                        if (
                            map_layer.get("type", "") == "raster"
                            or map_layer["layerId"] != layer.id
                        ):
                            continue
                        if map_layer["source-layer"] != sub_source.slug:
                            continue
                        map_layer["source"] = sub_source_id

            geolayer = layer.source.get_layer()
            url = reverse("layer-tilejson", args=(geolayer.id,))
            source_id = f"{self.DEFAULT_SOURCE_NAME}_{i}"
            custom_style_infos.append((url, source_id))

            # Set the correct source "id" for each non-raster layer in the customStyle field
            for map_layer in layer_structure["map"]["customStyle"]["layers"]:
                if (
                    map_layer.get("type", "") == "raster"
                    or map_layer["layerId"] != layer.id
                ):
                    continue
                if map_layer["source-layer"] != layer.source.slug:
                    continue
                map_layer["source"] = source_id

        layer_structure["map"]["customStyle"]["sources"] = [
            {
                "id": source_id,
                "type": self.DEFAULT_SOURCE_TYPE,
                "url": f"{url}?{querystring.urlencode()}",
            }
            for url, source_id in custom_style_infos
        ]

        layer_structure["styleImages"] = StyleImageSerializer(
            StyleImage.objects.filter(
                layer__in=self.scene.layers.values_list("pk", flat=True)
            ),
            many=True,
            context={"request": self.request},
        ).data

        return layer_structure

    def get_map_settings(self, scene):
        default_map_settings = {
            "accessToken": config.MAPBOX_ACCESS_TOKEN,
            "center": [config.MAP_DEFAULT_LNG, config.MAP_DEFAULT_LAT],
            "zoom": config.MAP_DEFAULT_ZOOM,
            "maxZoom": config.MAP_MAX_ZOOM,
            "minZoom": config.MAP_MIN_ZOOM,
            "fitBounds": {
                "coordinates": [
                    [config.MAP_BBOX_LNG_MIN, config.MAP_BBOX_LAT_MIN],
                    [config.MAP_BBOX_LNG_MAX, config.MAP_BBOX_LAT_MAX],
                ]
            },
        }
        """Return the default map settings overridden with map settings from the scene if present"""
        if "map_settings" in scene.config:
            return {
                **default_map_settings,
                **scene.config["map_settings"],
            }
        return default_map_settings

    def get_layer_structure(self):
        """Return the structured layerTree"""
        layer_structure = {
            "title": self.scene.name,
            "type": self.scene.category,
            "layersTree": self.get_layers_tree(self.scene),
            "interactions": self.get_interactions(self.layers),
            "map": {
                **self.get_map_settings(self.scene),
                "customStyle": {"sources": [], "layers": self.get_map_layers()},
            },
        }

        # settings are merged for now
        map_base_layers = (
            self.scene.base_layers.all()
            if self.scene.base_layers.all()
            else MapBaseLayer.objects.all()
        )
        baselayers = [
            {
                "id": baselayer.id,
                "label": baselayer.name,
                "url": self.request.build_absolute_uri(baselayer.url)
                if baselayer.base_layer_type != "mapbox"
                else baselayer.url,
            }
            for baselayer in map_base_layers
        ]

        # avoid futur reference modifications
        map_structure = deepcopy(layer_structure["map"])
        background_styles = map_structure.get("backgroundStyle", [])

        # If no base layer, we use default one
        if not baselayers:
            if type(background_styles) is list:
                # background_styles += baselayers
                baselayers = background_styles
            else:
                # backgroundStyles can be just an url
                baselayers = [{"label": "", "url": background_styles}]

        layer_structure["map"]["backgroundStyle"] = baselayers

        return layer_structure

    def get_map_layers(self):
        """Return sources information using serializer from sources_serializers module"""
        map_layers = []
        for layer in self.layers.filter(
            source__slug__in=self.authorized_sources
        ).prefetch_related(
            Prefetch(
                "extra_styles",
                queryset=CustomStyle.objects.filter(
                    source__slug__in=self.authorized_sources
                ),
                to_attr="authorized_extra_styles",
            )
        ):
            map_layers += [
                dict(
                    **SourceSerializer.get_object_serializer(layer).data,
                    layerId=layer.id,
                ),
                *[
                    dict(
                        **SourceSerializer.get_object_serializer(cs).data,
                        layerId=layer.id,
                    )
                    for cs in layer.authorized_extra_styles
                ],
            ]
        return map_layers

    def get_interactions(self, layers):
        """Return interactions for all layers in the scene"""
        interactions = []
        for layer in layers:
            interactions += self.get_interactions_for_layer(layer)
        return interactions

    def get_formatted_interactions(self, layer):
        """Return all interactions of a layer after beeing formatted correctly
        for the frontend
        """
        return [
            {
                "id": layer.layer_identifier,
                "fetchProperties": {
                    "url": unquote(
                        reverse(
                            "feature-detail",
                            args=(layer.source.get_layer().pk, "{{id}}"),
                        )
                    ),
                    "id": "_id",
                },
                **interaction,
            }
            for interaction in layer.interactions
        ]

    def get_interactions_for_layer(self, layer):
        """Return formatted interaction of a layer

        It contains, popup, minisheet and custom styles
        """
        interactions = self.get_formatted_interactions(layer)
        for cs in layer.extra_styles.all():
            interactions += self.get_formatted_interactions(cs)

        main_field = getattr(layer.main_field, "name", None)

        if layer.popup_config.get("enable"):
            interactions.append(
                {
                    "id": layer.layer_identifier,
                    "mainField": main_field,
                    "clusterLabel": main_field,  # Kept for compatibility purpose
                    "interaction": "displayTooltip",
                    "trigger": "mouseover",
                    "template": layer.popup_config.get("template"),
                    "constraints": [
                        {
                            "minZoom": layer.popup_config.get("minzoom"),
                            "maxZoom": layer.popup_config.get("maxzoom"),
                        },
                    ],
                }
            )

        if layer.minisheet_config.get("enable"):
            settings_interactions = {
                "id": layer.layer_identifier,
                "mainField": main_field,
                "clusterLabel": main_field,  # Kept for compatibility purpose
                "interaction": "displayDetails",
                "template": layer.minisheet_config.get("template", ""),
                "fetchProperties": {
                    "url": unquote(
                        reverse(
                            "feature-detail",
                            args=(layer.source.get_layer().pk, "{{id}}"),
                        )
                    ),
                    "id": "_id",
                },
            }
            if layer.minisheet_config.get("highlight_color"):
                settings_interactions["highlight_color"] = layer.minisheet_config[
                    "highlight_color"
                ]

            interactions.append(settings_interactions)

        return interactions

    def get_layers_list_for_layer(self, layer):
        """Return list of sublayers of a layer"""
        return [
            layer.layer_identifier,
            *[s.layer_identifier for s in layer.extra_styles.all()],
        ]

    def get_layers_tree(self, scene):
        """Return the full layer tree of a scene object"""
        root_group = LayerGroup.objects.prefetch_related(self.prefetch_layers).get(
            view=scene, parent=None
        )

        # Keep only child of root group
        return self.get_group_dict(root_group)["layers"]

    def get_group_dict(self, group):
        """Recursive method that return the tree from a LayerGroup element.

        `group.settings` is injected in the group dictionary, so any setting can be overridden.

        """
        group_content = {
            "group": group.label,
            "exclusive": group.exclusive,
            "byVariable": group.by_variable,
            "variables": group.variables,
            "selectors": group.selectors,
            "order": group.order,
            "layers": [],
            **group.settings,
        }

        # Add subgroups
        for sub_group in group.children.filter(view=group.view).prefetch_related(
            self.prefetch_layers
        ):
            group_dict = self.get_group_dict(sub_group)
            # exclude empty groups
            if group_dict["layers"]:
                group_content["layers"].append(group_dict)

        # Add layers of group
        for layer in group.layers.filter(in_tree=True):
            layer_dict = self.get_layer_dict(layer)
            if layer_dict:
                group_content["layers"].append(layer_dict)

        # Group en layer ordering
        group_content["layers"].sort(key=lambda x: x["order"])

        # Remove key order as not part of schema
        [item.pop("order") for item in group_content["layers"]]

        return group_content

    def get_layer_dict(self, layer):
        if (
            layer.source.slug not in self.authorized_sources
            or layer.extra_styles.exclude(
                source__slug__in=self.authorized_sources
            ).exists()
        ):
            # Exclude layers with non-authorized sources
            return None

        default_values = {
            "initialState": {
                "active": layer.active_by_default,
                "opacity": layer.settings.get("default_opacity", 100) / 100,
            }
        }

        main_field = getattr(layer.main_field, "name", None)

        # Construct the layer object
        layer_object = {
            **dict_merge(default_values, layer.settings),
            "id": layer.id,
            "label": layer.name,
            "order": layer.order,
            "content": layer.description,
            "source_filter": layer.source_filter,
            "layers": self.get_layers_list_for_layer(layer),
            "legends": layer.legends,
            "variables": layer.variables,
            "mainField": main_field,
            "filters": {
                "layer": layer.source.slug,
                "layerId": layer.id,
                "mainField": main_field,
                "fields": self.get_filter_fields_for_layer(layer),
                "form": self.get_filter_forms_for_layer(layer),
            },
            "source_credit": layer.source.credit,
        }

        # Set the exportable status of the layer if any filter fields is exportable
        layer_object["filters"]["exportable"] = layer.table_export_enable and any(
            [f["exportable"] for f in layer_object["filters"]["fields"] or []]
        )

        return layer_object

    def get_filter_fields_for_layer(self, layer):
        """Return the filter fields of the layer if table is enabled"""

        if layer.table_enable:
            return [
                {
                    "value": field_filter.field.name,
                    "label": field_filter.label or field_filter.field.label,
                    "exportable": field_filter.exportable,
                    "format_type": field_filter.format_type
                    or TYPE_MAP[field_filter.field.data_type],
                    "display": field_filter.display,
                    "settings": field_filter.settings,
                }
                for field_filter in layer.filters_shown
            ]

    def get_filter_forms_for_layer(self, layer):
        """Return forms of a layer if filters are enabled"""
        if layer.filters_enabled:
            filter_list = [
                {
                    "property": field_filter.field.name,
                    "label": field_filter.label or field_filter.field.label,
                    **field_filter.filter_settings,
                }
                for field_filter in layer.filters_enabled
            ]
            # Respect filter defined order
            filter_list.sort(key=lambda f: f.get("order", 0))
            return filter_list

    @cached_property
    def authorized_sources(self):
        """Cached property of authorized sources from the authenticated user's groups"""
        return list(
            self.layergroup.layers.filter(
                Q(authorized_groups__isnull=True)
                | Q(authorized_groups__in=self.user_groups)
            ).values_list("name", flat=True)
        )

    @cached_property
    def layers(self):
        """List of layers of the selected scene"""
        layers = (
            Layer.objects.filter(group__view=self.scene.pk)
            .order_by("order")
            .select_related("source")
            .prefetch_related("extra_styles__source")
        )

        if layers:
            return layers
        raise Http404
