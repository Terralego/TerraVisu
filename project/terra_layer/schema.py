import jsonschema
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator


class JSONSchemaValidator(BaseValidator):
    def compare(self, a, b):
        try:
            jsonschema.validate(a, b)
        except jsonschema.exceptions.ValidationError:
            msg = f"{a} failed JSON schema check"
            raise ValidationError(msg)


SCENE_LAYERTREE = {
    "definitions": {},
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://terralego.com/scene_layertree.json",
    "type": "array",
    "title": "Scene layer tree schema",
    "items": {
        "$id": "#/items",
        "type": "object",
        "title": "Layer tree item",
        "required": [],
        "dependencies": {"group": ["children", "label"]},
        "properties": {
            "label": {
                "$id": "#/items/properties/label",
                "type": "string",
                "title": "The group name",
                "default": "",
                "examples": ["My Group"],
                "pattern": "^(.*)$",
            },
            "expanded": {
                "$id": "#/items/properties/expanded",
                "type": "boolean",
                "title": "The expanded status in admin. Not used yet",
                "default": False,
                "examples": [True],
            },
            "geolayer": {
                "$id": "#/items/properties/geolayer",
                "type": "integer",
                "title": "The geolayer id",
                "default": 0,
                "examples": [96],
            },
            "group": {
                "$id": "#/items/properties/group",
                "type": "boolean",
                "title": "The group name. Present if it's a group.",
                "default": False,
                "examples": [True],
            },
            "selectors": {
                "$id": "#/items/properties/selectors",
                "type": ["array", "null"],
                "title": "The selectors for this group",
            },
            "settings": {
                "$id": "#/items/properties/settings",
                "type": "object",
                "title": "The settings of group",
            },
            "children": {"$ref": "#"},
        },
    },
}
