from os.path import basename

import psycopg2
import requests
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.utils.translation import gettext as _
from psycopg2 import sql
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    CommandSource,
    CSVSource,
    Field,
    GeoJSONSource,
    GeometryTypes,
    PostGISSource,
    ShapefileSource,
    Source,
    SourceReporting,
    WMTSSource,
)


class PolymorphicModelSerializer(serializers.ModelSerializer):
    type_field = "_type"
    type_class_map = {}

    def __new__(cls, *args, **kwargs):
        """
        Return the correct serializer given the type provided in type_field
        """
        if kwargs.pop("many", False):
            return cls.many_init(*args, **kwargs)

        if "data" in kwargs:
            data_type = kwargs["data"].get(cls.type_field)

            serializer = cls.get_serializer_from_type(data_type)

            if serializer is not cls:
                return serializer(*args, **kwargs)

        return super().__new__(cls, *args, **kwargs)

    def __init_subclass__(cls, **kwargs):
        """Create a registry of all subclasses of the current class"""
        if cls.Meta.model:
            cls.type_class_map[cls.Meta.model.__name__] = cls

    @classmethod
    def get_serializer_from_type(cls, data_type):
        """
        Returns the serializer class from datatype
        """
        if data_type in cls.type_class_map:
            return cls.type_class_map[data_type]
        raise ValidationError({cls.type_field: f"{data_type}'s type is unknown"})

    def to_representation(self, obj):
        serializer = self.get_serializer_from_type(obj.__class__.__name__)

        if serializer is self.__class__:
            data = {
                k: v
                for k, v in super().to_representation(obj).items()
                if k not in obj.polymorphic_internal_model_fields
            }
        else:
            data = serializer().to_representation(obj)

        data[self.type_field] = obj.__class__.__name__

        return data

    def to_internal_value(self, data):
        data_type = data.get(self.type_field)

        validated_data = super().to_internal_value(data)

        validated_data[self.type_field] = data_type

        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        data_type = validated_data.pop(self.type_field, None)
        serializer = self.get_serializer_from_type(data_type)(validated_data)

        if serializer.__class__ is self.__class__:
            return super().create(validated_data)
        else:
            return serializer.create(validated_data)


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        exclude = ("source",)
        read_only_fields = ("name", "sample", "source")


class SourceReportingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = SourceReporting


class SourceSerializer(PolymorphicModelSerializer):
    fields = FieldSerializer(many=True, required=False)
    slug = serializers.SlugField(max_length=255, read_only=True)
    report = SourceReportingSerializer(read_only=True)

    class Meta:
        fields = "__all__"
        model = Source
        extras = {"read_only": {"status": True}}

    def _update_fields(self, source):
        if source.run_sync_method("update_fields", success_state="NEED_SYNC").result:
            return source
        raise ValidationError("Fields update failed")

    @transaction.atomic
    def create(self, validated_data):
        # Fields can't be defined at source creation
        validated_data.pop("fields", None)
        source = super().create(validated_data)
        return self._update_fields(source)

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop("fields")

        source = super().update(
            instance, {**validated_data, "status": Source.Status.NEED_SYNC}
        )

        if source.report:
            source.report.reset()
            source.report.status = SourceReporting.Status.PENDING
            source.report.save()

        self._update_fields(source)

        for field_data in self.get_initial().get("fields", []):
            try:
                instance = source.fields.get(name=field_data.get("name"))
                serializer = FieldSerializer(instance=instance, data=field_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    raise ValidationError("Field configuration is not valid")
            except Field.DoesNotExist:
                pass

        return source


class SourceListSerializer(serializers.ModelSerializer):
    _type = serializers.SerializerMethodField()
    report = SourceReportingSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Source
        fields = (
            "id",
            "_type",
            "status",
            "name",
            "geom_type",
            "report",
        )

    def get__type(self, instance):
        return instance.__class__.__name__

    def get_status(self, instance):
        return instance.refresh_status


class PostGISSourceSerializer(SourceSerializer):
    id_field = serializers.CharField(required=False)
    geom_field = serializers.CharField(required=False, allow_null=True)

    def _get_connection(self, data):
        conn = psycopg2.connect(
            user=data.get("db_username"),
            password=data.get("db_password"),
            host=data.get("db_host"),
            port=data.get("db_port", 5432),
            dbname=data.get("db_name"),
        )
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _first_record(self, data):
        cursor = self._get_connection(data)
        query = "SELECT * FROM ({}) q LIMIT 1"
        cursor.execute(sql.SQL(query).format(sql.SQL(data["query"])))
        return cursor.fetchone()

    def _validate_geom(self, data):
        """Validate that geom_field exists else try to find it in source"""
        first_record = self._first_record(data)

        if data.get("geom_field") is None:
            for k, v in first_record.items():
                try:
                    geom = GEOSGeometry(v)
                    if geom.geom_typeid == data.get("geom_type"):
                        data["geom_field"] = k
                        break
                except Exception:
                    pass

            else:
                geomtype_name = GeometryTypes(data.get("geom_type")).name
                raise ValidationError(f"No geom field found of type {geomtype_name}")
        elif data.get("geom_field") not in first_record:
            raise ValidationError("Field does not exist in source")

        return data

    def _validate_query_connection(self, data):
        """Check if connection information are valid or not, trying to
        connect to the Pg server and executing the query
        """
        try:
            if self.instance and not data.get("db_password"):
                data["db_password"] = self.instance.db_password
            self._first_record(data)
        except Exception:
            raise ValidationError("Connection informations or query are not valid")

    def validate(self, data):
        self._validate_query_connection(data)
        data = self._validate_geom(data)

        return super().validate(data)

    class Meta:
        model = PostGISSource
        fields = "__all__"
        extra_kwargs = {"db_password": {"write_only": True}}


class FileSourceSerializer(SourceSerializer):
    filename = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        if len(data.get("file", [])) > 0:
            data["file"] = data["file"][0]

        return super().to_internal_value(data)

    def get_filename(self, instance):
        if instance.file:
            return basename(instance.file.name)

    class Meta:
        model = None


class GeoJSONSourceSerializer(FileSourceSerializer):
    class Meta:
        model = GeoJSONSource
        fields = "__all__"
        extra_kwargs = {"file": {"write_only": True}}

    def _validate_field_infos(self, data):
        # remove _type field as it is not needed by the model
        # but it's must stay in the data used later by the serializer
        data_copy = {**data}
        data_copy.pop("_type")
        if data_copy.get("fields") and not data_copy.get("file"):
            return  # file fields is empty in update
        # create an instance without saving data
        try:
            instance = self.Meta.model(**data_copy)
        except TypeError:
            return  # file field is empty in update no get_records
        try:
            records, _ = instance._get_records(1)
        except Exception as err:
            raise ValidationError(err.args[0])

        # validating id in records
        for i, row in enumerate(records):
            try:
                _ = row[instance.id_field]  # noqa
            except Exception:
                raise ValidationError(
                    f"Can't find identifier field at the record index {i}"
                )

    def validate(self, data):
        self._validate_field_infos(data)
        return super().validate(data)


class ShapefileSourceSerializer(FileSourceSerializer):
    class Meta:
        model = ShapefileSource
        fields = "__all__"
        extra_kwargs = {"file": {"write_only": True}}


class CommandSourceSerializer(SourceSerializer):
    class Meta:
        model = CommandSource
        fields = "__all__"
        extra_kwargs = {"command": {"read_only": True}}


class WMTSSourceSerialize(SourceSerializer):
    minzoom = serializers.IntegerField(
        min_value=0, max_value=24, allow_null=True, default=0
    )
    maxzoom = serializers.IntegerField(
        min_value=0, max_value=24, allow_null=True, default=24
    )
    geom_type = serializers.CharField(required=False, allow_null=True, default=None)
    status = serializers.SerializerMethodField()

    class Meta:
        model = WMTSSource
        fields = "__all__"

    def validate(self, data):
        # We do not use validate_url hook method
        # we wan't to return a non_field_errors for the front-end
        # replace x,y,z placeholder with value in the wmts url
        url = (
            data.get("url", "")
            .replace("{z}", "1")
            .replace("{y}", "1")
            .replace("{x}", "1")
        )
        try:
            requests.get(url)
        except requests.ConnectionError:
            raise ValidationError("Can't reach specified tile server. Check your url.")

        return super().validate(data)

    def get_status(self, instance):
        return instance.get_status().get("state")


class CSVSourceSerializer(FileSourceSerializer):
    coordinate_reference_system = serializers.CharField(required=True)
    encoding = serializers.CharField(required=True)
    field_separator = serializers.CharField(required=True)
    decimal_separator = serializers.CharField(required=True)
    char_delimiter = serializers.CharField(required=True)
    coordinates_field = serializers.CharField(required=True)
    number_lines_to_ignore = serializers.IntegerField(required=True)
    use_header = serializers.BooleanField(required=False, default=False)
    ignore_columns = serializers.BooleanField(required=False, default=False)
    latitude_field = serializers.CharField(required=False)
    longitude_field = serializers.CharField(required=False)
    latlong_field = serializers.CharField(required=False)
    coordinates_field_count = serializers.CharField(required=False)
    coordinates_separator = serializers.CharField(required=False)
    geom_type = serializers.ChoiceField(
        default=GeometryTypes.Point, choices=GeometryTypes.choices()
    )

    class Meta:
        model = CSVSource
        fields = "__all__"
        extra_kwargs = {
            "file": {"write_only": True},
        }

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        # settings does not exist if no group is specified at creation
        settings = validated_data.get("settings", {})
        settings.update(
            {
                "coordinate_reference_system": validated_data.pop(
                    "coordinate_reference_system"
                ),
                "encoding": validated_data.pop("encoding"),
                "field_separator": validated_data.pop("field_separator"),
                "decimal_separator": validated_data.pop("decimal_separator"),
                "char_delimiter": validated_data.pop("char_delimiter"),
                "coordinates_field": validated_data.get("coordinates_field"),
                "number_lines_to_ignore": validated_data.pop("number_lines_to_ignore"),
                "use_header": validated_data.pop("use_header"),
                "ignore_columns": validated_data.pop("ignore_columns"),
            }
        )
        if validated_data.get("coordinates_field") == "one_column":
            settings.update(
                {
                    "latlong_field": validated_data.pop("latlong_field"),
                    "coordinates_field_count": validated_data.pop(
                        "coordinates_field_count"
                    ),
                    "coordinates_separator": validated_data.pop(
                        "coordinates_separator"
                    ),
                }
            )

        elif validated_data.get("coordinates_field") == "two_columns":
            settings.update(
                {
                    "latitude_field": validated_data.pop("latitude_field"),
                    "longitude_field": validated_data.pop("longitude_field"),
                }
            )
        validated_data.pop("coordinates_field")
        validated_data["settings"] = settings
        return validated_data

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if data.get("coordinates_field") == "one_column":
            data.pop("latitude_field")
            data.pop("longitude_field")

        if data.get("coordinates_field") == "two_columns":
            data.pop("latlong_field")
            data.pop("coordinates_field_count")
            data.pop("coordinates_separator")
        return data

    def _validate_field_infos(self, data):
        # remove _type field as it is not needed by the model
        # but it's must stay in the data used later by the serializer
        data_copy = {**data}
        data_copy.pop("_type")
        if data_copy.get("fields") and not data_copy.get("file"):
            return  # file fields is empty in update
        # create an instance without saving data
        instance = self.Meta.model(**data_copy)
        try:
            records, _ = instance._get_records(1)
        except (ValueError, GDALException) as err:
            raise ValidationError(err.args[0])

        # validating id in records
        for row in records:
            try:
                _ = row[instance.id_field]  # noqa
            except KeyError:
                raise ValidationError(
                    "Can't find identifier field in one or more records"
                )

    def validate(self, data):
        # do not use this for now as it cause file creation to bug
        # FileNotFoundError is raised with the wrong file path
        # self._validate_field_infos(data)
        validated_data = super().validate(data)
        if data["settings"]["coordinates_field"] == "one_column":
            if not data["settings"].get("latlong_field"):
                raise ValidationError(
                    _(
                        "latlong_field must be defined when coordinates are set to one column"
                    )
                )
            if not data["settings"].get("coordinates_field_count"):
                raise ValidationError(
                    _(
                        "Coordinates order must be specified when coordinates are set to one column"
                    )
                )
            if not data["settings"].get("coordinates_separator"):
                raise ValidationError(
                    _(
                        "Coordinates separator must be specified when coordinates are set to one column"
                    )
                )
        elif data["settings"]["coordinates_field"] == "two_columns":
            if not data["settings"].get("latitude_field"):
                raise ValidationError(
                    _(
                        "Latitude field must be specified when coordinates are set to two columns"
                    )
                )
            if not data["settings"].get("longitude_field"):
                raise ValidationError(
                    _(
                        "Longitude field must be specified when coordinates are set to two columns"
                    )
                )
        else:
            raise ValidationError(_("Incorrect value for coordinates field"))
        return validated_data
