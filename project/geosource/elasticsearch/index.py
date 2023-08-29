import json
import logging
from collections import defaultdict

from project.geosource.elasticsearch import ESMixin

logger = logging.getLogger(__name__)


class LayerESIndex(ESMixin):
    def __init__(self, layer, client=None):
        self.layer = layer
        self.client = self.get_client() if not client else client

    def index(self):
        self.clean_index()
        self.create_index()

    def _get_formatted_record(self, index, feature):
        return {
            "index": index,
            "id": feature.identifier,
            "document": {
                "_feature_id": feature.identifier,
                "geom": json.loads(feature.geom.geojson),
                **feature.properties,
            },
        }

    def index_feature(self, layer, feature):
        record = self._get_formatted_record(layer.name, feature)
        self.client.index(**record)

    def clean_index(self):
        self.client.indices.delete(index=self.layer.name, ignore=[400, 404])

    def create_index(self):
        """
        Create ES index with specified type mapping from layer source
        If mapping not available, we switch on ES type guessing
        """
        from project.geosource.models import FieldTypes, Source

        try:
            s = Source.objects.get(slug=self.layer.name)
        except Source.DoesNotExist:
            # If no source, we ignore it. Type will be guessed later.
            return

        logger.info(f"Index creation for layer {self.layer.name}")

        type_mapping = defaultdict(lambda: "text")
        type_mapping["integer"] = "long"
        type_mapping["float"] = "float"
        type_mapping["boolean"] = "boolean"
        type_mapping["date"] = "date"

        # Get type from source field configuration. Ignore undefined types.
        field_conf = {}
        for field in s.fields.all():
            # if field.data_type != 5:
            field_type = type_mapping[FieldTypes(field.data_type).name.lower()]
            if field_type == "text":
                # Exception for text field, we also want them to be keyword accessible
                field_conf[field.name] = {
                    "type": field_type,
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                }
            else:
                field_conf[field.name] = {"type": field_type}

        # Add geom default type mapping
        field_conf["geom"] = {"type": "geo_shape", "ignore_z_value": True}

        # Create query body with mapping
        body = {"mappings": {"properties": field_conf}}

        try:
            self.client.indices.create(index=self.layer.name, body=body)
        except Exception:
            logger.exception("ES index for layer {layer.name} can't be created")
