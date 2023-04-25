import json
import sys
from datetime import date, timedelta
from enum import Enum, auto
from io import BytesIO

import fiona
import psycopg2
import pyexcel
from celery.result import AsyncResult
from celery.utils.log import LoggingProxy
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSGeometry
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from geostore import GeometryTypes
from polymorphic.models import PolymorphicModel
from psycopg2 import sql

from .callbacks import get_attr_from_path
from .elasticsearch.index import LayerESIndex
from .fields import LongURLField
from .mixins import CeleryCallMethodsMixin
from .signals import refresh_data_done

# Decimal fields must be returned as float
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(DEC2FLOAT)


class FieldTypes(Enum):
    String = auto()
    Integer = auto()
    Float = auto()
    Boolean = auto()
    Undefined = auto()
    Date = auto()

    @classmethod
    def choices(cls):
        return [(enum.value, enum) for enum in cls]

    @classmethod
    def get_type_from_data(cls, data):
        types = {
            type(None): cls.Undefined,
            str: cls.String,
            int: cls.Integer,
            bool: cls.Boolean,
            float: cls.Float,
            date: cls.Date,
        }

        return types.get(type(data), cls.Undefined)


class Source(PolymorphicModel, CeleryCallMethodsMixin):
    name = models.CharField(max_length=255, unique=True)
    credit = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    id_field = models.CharField(max_length=255, default="id")
    geom_type = models.IntegerField(
        choices=GeometryTypes.choices(), null=True, blank=True
    )

    settings = models.JSONField(default=dict, blank=True)
    groups = models.ManyToManyField(Group, blank=True, related_name="geosources")
    report = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)

    task_id = models.CharField(null=True, max_length=255, blank=True)
    task_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_refresh = models.DateTimeField(default=timezone.now)

    SOURCE_GEOM_ATTRIBUTE = "_geom_"
    MAX_SAMPLE_DATA = 5

    def get_layer(self):
        return get_attr_from_path(settings.GEOSOURCE_LAYER_CALLBACK)(self)

    def update_feature(self, *args):
        return get_attr_from_path(settings.GEOSOURCE_FEATURE_CALLBACK)(self, *args)

    def clear_features(self, layer, begin_date):
        return get_attr_from_path(settings.GEOSOURCE_CLEAN_FEATURE_CALLBACK)(
            self, layer, begin_date
        )

    def delete(self, *args, **kwargs):
        get_attr_from_path(settings.GEOSOURCE_DELETE_LAYER_CALLBACK)(self)
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def should_refresh(self):
        now = timezone.now()
        if not getattr(self, "refresh", None) or self.refresh < 1:
            return False
        next_run = self.last_refresh + timedelta(minutes=self.refresh)
        return next_run < now

    def refresh_data(self):
        layer = self.get_layer()
        try:
            es_index = LayerESIndex(layer)
            es_index.index()
            response = self._refresh_data(es_index)
            return response
        finally:
            self.last_refresh = timezone.now()
            self.save()
            refresh_data_done.send_robust(
                sender=self.__class__,
                layer=layer.pk,
            )

    def _refresh_data(self, es_index=None):
        report = {}

        layer = self.get_layer()
        begin_date = timezone.now()
        row_count = 0
        total = 0
        for i, row in enumerate(self._get_records()):
            total += 1
            geometry = row.pop(self.SOURCE_GEOM_ATTRIBUTE)
            try:
                identifier = row[self.id_field]
                try:
                    sid = transaction.savepoint()
                    feature = self.update_feature(layer, identifier, geometry, row)
                    if es_index and feature:
                        es_index.index_feature(layer, feature)
                    transaction.savepoint_commit(sid)
                except Exception as exc:
                    transaction.savepoint_rollback(sid)
                    msg = "An error occured on feature(s)"
                    report["status"] = "Warning"
                    report.setdefault("message", []).append(msg)
                    report.setdefault("lines", {})[
                        f"Error on row n°{i} {self.id_field} : {identifier}"
                    ] = str(exc)
                    continue
            except KeyError:
                msg = "Can't find identifier field for this record"
                report["status"] = "Warning"
                report.setdefault("message", []).append(msg)
                report.setdefault("lines", {})[i] = msg
                continue
            row_count += 1
        self.clear_features(layer, begin_date)

        self.report = report
        if not self.report:
            if not row_count:
                self.report["status"] = "Error"
                self.save(update_fields=["report"])
                raise Exception("Failed to refresh data")

            if row_count == total:
                self.report["status"] = "SUCCESS"
                self.save(update_fields=["report"])
        return {"count": row_count, "total": total}

    @transaction.atomic
    def update_fields(self):
        records = self._get_records(50)

        fields = {}

        for record in records:
            record.pop(self.SOURCE_GEOM_ATTRIBUTE)

            for i, (field_name, value) in enumerate(record.items()):
                is_new = False

                if field_name not in fields:
                    field, is_new = self.fields.get_or_create(
                        name=field_name,
                        defaults={"label": field_name},
                    )
                    field.order = i  # force order for update
                    field.sample = []
                    fields[field_name] = field

                if is_new or fields[field_name].data_type == FieldTypes.Undefined:
                    fields[field_name].data_type = FieldTypes.get_type_from_data(
                        value
                    ).value

                if (
                    len(fields[field_name].sample) < self.MAX_SAMPLE_DATA
                    and value is not None
                ):
                    if isinstance(value, bytes):
                        try:
                            value = value.decode()
                        except (UnicodeDecodeError, AttributeError):
                            msg = f"{field_name} couldn't be decoded for source {self.name}"
                            self.report["status"] = "Warning"
                            self.report.setdefault("lines", {}).setdefault(
                                f"{i}", []
                            ).append(msg)
                            self.save()
                            continue

                    fields[field_name].sample.append(value)

        for field in fields.values():
            field.save()

        # Delete fields that are not anymore present
        self.fields.exclude(name__in=fields.keys()).delete()

        return {"count": len(fields)}

    def get_status(self):
        response = {}

        if self.task_id:
            task = AsyncResult(self.task_id)
            response = {"state": task.state, "done": task.date_done}

            if task.successful():
                response["result"] = task.result
            if task.failed():
                response["result"] = {"error": str(task.result)}

        return response

    def _get_records(self, limit=None):
        raise NotImplementedError

    def __str__(self):
        return f"{self.name} - {self.__class__.__name__}"

    @property
    def type(self):
        return self.__class__


class Field(models.Model):
    source = models.ForeignKey(Source, related_name="fields", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    label = models.CharField(max_length=255)
    data_type = models.IntegerField(
        choices=FieldTypes.choices(), default=FieldTypes.Undefined.value
    )
    level = models.IntegerField(default=0)
    sample = models.JSONField(default=list, encoder=DjangoJSONEncoder, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.source.name} - {self.data_type})"

    class Meta:
        unique_together = ["source", "name"]
        ordering = ("order",)


class PostGISSource(Source):
    db_host = models.CharField(
        max_length=255,
    )
    db_port = models.IntegerField(default=5432)
    db_username = models.CharField(max_length=63)
    db_password = models.CharField(max_length=255)
    db_name = models.CharField(max_length=63)

    query = models.TextField()

    geom_field = models.CharField(max_length=255)

    refresh = models.IntegerField(default=-1)

    @property
    def SOURCE_GEOM_ATTRIBUTE(self):
        return self.geom_field

    @property
    def _db_connection(self):
        try:
            conn = psycopg2.connect(
                user=self.db_username,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
            )
        except psycopg2.errors.OperationalError as err:
            self.report["status"] = "Error"
            self.report.setdefault("message", []).append(err.args[0])
            self.save()
            raise
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _get_records(self, limit=None):
        cursor = self._db_connection

        query = "SELECT * FROM ({}) q "
        attrs = [sql.SQL(self.query)]
        if limit:
            query += "LIMIT {}"
            attrs.append(sql.Literal(limit))

        cursor.execute(sql.SQL(query).format(*attrs))

        return cursor


class GeoJSONSource(Source):
    file = models.FileField(upload_to="geosource/geojson/%Y/")

    def get_file_as_dict(self):
        try:
            return json.load(self.file)
        except json.JSONDecodeError:
            msg = "Source's GeoJSON file is not valid"
            self.report["status"] = "Error"
            self.report.setdefault("message", []).append(msg)
            self.save()
            raise

    def _get_records(self, limit=None):
        geojson = self.get_file_as_dict()

        limit = limit if limit else len(geojson["features"])

        records = []
        for i, record in enumerate(geojson["features"][:limit]):
            try:
                records.append(
                    {
                        self.SOURCE_GEOM_ATTRIBUTE: GEOSGeometry(
                            json.dumps(record["geometry"])
                        ),
                        **record["properties"],
                    }
                )
            except (ValueError, GDALException):
                msg = "The record geometry seems invalid."
                self.report["status"] = "Warning"
                self.report.setdefault("line", {}).setdefault(f"{i}", []).append(msg)
                self.save()
                raise ValueError(msg)

        return records


class ShapefileSource(Source):
    # Zipped ShapeFile
    file = models.FileField(upload_to="geosource/shapefile/%Y/")

    def _get_records(self, limit=None):
        with fiona.BytesCollection(self.file.read()) as shapefile:
            limit = limit if limit else len(shapefile)

            # Detect the EPSG
            _, srid = shapefile.crs.get("init", "epsg:4326").split(":")

            # Return geometries with a hack to set the correct geometry srid
            return [
                {
                    self.SOURCE_GEOM_ATTRIBUTE: GEOSGeometry(
                        GEOSGeometry(json.dumps(feature.get("geometry"))).wkt,
                        srid=int(srid),
                    ),
                    **feature.get("properties", {}),
                }
                for feature in shapefile[:limit]
            ]


class CommandSource(Source):
    command = models.CharField(max_length=255)

    def _refresh_data(self, es_index=None):
        layer = self.get_layer()
        begin_date = timezone.now()

        try:
            # whether we are in a celery task ?
            if isinstance(sys.stdout, LoggingProxy):
                # Hack to be able to launch command with mondrian logging
                sys.stdout.buffer = BytesIO()
                sys.stdout.encoding = None
                sys.stderr.buffer = BytesIO()
                sys.stderr.encoding = None
        except AttributeError:
            pass

        call_command(self.command, source=self.pk)

        self.clear_features(layer, begin_date)

        refresh_data_done.send_robust(sender=self.__class__, layer=layer.pk)

        return {"count": layer.features.count()}

    def _get_records(self, limit=None):
        return []


class WMTSSource(Source):
    minzoom = models.IntegerField(null=True)
    maxzoom = models.IntegerField(null=True)
    tile_size = models.IntegerField()
    url = LongURLField()

    def get_status(self):
        return {"state": "DONT_NEED"}

    def refresh_data(self):
        return {}

    def _get_records(self, limit=None):
        return []


class CSVSource(Source):
    SEPARATORS = {
        "comma": ",",
        "semicolon": ";",
        "tabulation": "\t",
        "space": " ",
        "column": ":",
        "doublequote": '"',
        "simplequote": "'",
        "point": ".",
    }
    file = models.FileField(upload_to="geosource/csv/%Y")

    def get_file_as_sheet(self):
        separator = self._get_separator(self.settings["field_separator"])
        quotechar = self._get_separator(self.settings["char_delimiter"])
        try:
            return pyexcel.get_sheet(
                file_name=self.file.path,
                delimiter=separator,
                encoding=self.settings["encoding"],
                quotechar=quotechar,
            )
        # Exception is raised if no parser found
        except (pyexcel.exceptions.FileTypeNotSupported, Exception) as err:
            msg = "Provided CSV file is invalid"
            self.report["status"] = "Error"
            self.report.setdefault("message", []).append(msg)
            self.save()
            err.args = (msg,)  # new message for the user
            raise

    def _get_records(self, limit=None):
        sheet = self.get_file_as_sheet()
        if self.settings.get("use_header"):
            sheet.name_columns_by_row(0)

        ignored_columns = []
        if self.settings.get("ignore_columns"):
            ignored_columns = self._get_null_columns_indexes(sheet)

        limit = limit if limit else len(sheet)

        records = []
        srid = self._get_srid()
        row_count = 0
        total = 0
        for i, row in enumerate(sheet):
            total += 1
            if self.settings["coordinates_field"] == "two_columns":
                lat_field = self.settings["latitude_field"]
                lng_field = self.settings["longitude_field"]

                x, y = self._extract_coordinates(
                    row, sheet.colnames, [lng_field, lat_field]
                )
                ignored_field = (row.index(x), row.index(y), *ignored_columns)
            else:
                lnglat_field = self.settings["latlong_field"]
                try:
                    x, y = self._extract_coordinates(
                        row, sheet.colnames, [lnglat_field]
                    )
                except ValueError:
                    continue
                coord_fields = (
                    (sheet.colnames.index(lnglat_field),)
                    if self.settings.get("use_header")
                    else (int(lnglat_field),)
                )
                ignored_field = (*coord_fields, *ignored_columns)

            cells = self._get_cells(sheet, row, ignored_field)
            try:
                records.append(
                    {
                        self.SOURCE_GEOM_ATTRIBUTE: GEOSGeometry(
                            f"Point({x} {y})", srid=srid
                        ),
                        **cells,
                    }
                )
            except (ValueError, GDALException):
                msg = f"One of source's record has invalid geometry: Point({x} {y}) srid={srid}"
                self.report["status"] = "Warning"
                self.report.setdefault("message", []).append(msg)
                self.save()
                # raise ValueError(msg)
                continue
            row_count += 1
        if not row_count:
            self.report["status"] = "Error"
            self.report.setdefault("message", []).append(
                "No record could be imported, check the report"
            )
        elif row_count == total:
            self.report["status"] = "SUCCESS"
        return records

    def _extract_coordinates(self, row, colnames, fields):
        coords = []
        for field in fields:
            # if no header, we expect index for the columns has been provided
            try:
                field_index = (
                    colnames.index(field)
                    if self.settings.get("use_header")
                    else int(field)
                )
            except ValueError as err:
                msg = f"{field} is not a valid coordinate field"
                self.report["status"] = "Warning"
                self.report.setdefault("message", []).append(msg)
                self.save()
                err.args = (msg,)
                raise
            c = row[field_index]
            coords.append(c)
        if len(coords) == 2:
            x, y = coords
        else:
            sep = self._get_separator(self.settings["coordinates_separator"])
            is_xy = self.settings["coordinates_field_count"] == "xy"
            # some fools use a reversed cartesian coordinates system (╯°□°)╯︵ ┻━┻
            x, y = coords[0].split(sep) if is_xy else coords[0].split(sep)[::-1]

        # correct formated decimal is required for GEOSGeometry
        if not self.settings["decimal_separator"] == "point":
            delimiter = self._get_separator(self.settings["decimal_separator"])
            x = x.replace(delimiter, ".")
            y = y.replace(delimiter, ".")

        return (x, y)

    def _get_null_columns_indexes(self, sheet):
        null_columns_indexes = []
        for i, column in enumerate(sheet.column):
            non_empty_cells = [cell for cell in column if cell != ""]
            (len(non_empty_cells) == 0) and null_columns_indexes.append(i)
        return null_columns_indexes

    def _get_cells(self, sheet, row, ingored_columns):
        if not self.settings.get("use_header"):
            # records names are the column index when no header was provided
            # casting to str to avoid issue (e.i id_field)
            return {
                str(i): self._format_cell_value(value)
                for i, value in enumerate(row)
                if i not in ingored_columns
            }

        return {
            name: self._format_cell_value(value)
            for i, (name, value) in enumerate(zip(sheet.colnames, row))
            if i not in ingored_columns
        }

    def _format_cell_value(self, value):
        return None if value == "" else value

    def _get_separator(self, name):
        return self.SEPARATORS[name]

    def _get_srid(self):
        coordinate_reference_system = self.settings["coordinate_reference_system"]
        try:
            return int(coordinate_reference_system.split("_")[1])
        except (IndexError, ValueError) as err:
            msg = f"Invalid SRID: {coordinate_reference_system}"
            self.report["status"] = "Error"
            self.report.setdefault("message", []).append(msg)
            self.save()
            err.args = (msg,)
            raise

    # properties are use by serializer for representation (reading operation)
    @property
    def coordinate_reference_system(self):
        return self.settings.get("coordinate_reference_system")

    @property
    def encoding(self):
        return self.settings.get("encoding")

    @property
    def field_separator(self):
        return self.settings.get("field_separator")

    @property
    def decimal_separator(self):
        return self.settings.get("decimal_separator")

    @property
    def char_delimiter(self):
        return self.settings.get("char_delimiter")

    @property
    def coordinates_field(self):
        return self.settings.get("coordinates_field")

    @property
    def number_lines_to_ignore(self):
        return self.settings.get("number_lines_to_ignore")

    @property
    def use_header(self):
        return self.settings.get("use_header")

    @property
    def ignore_columns(self):
        return self.settings.get("ignore_columns")

    @property
    def latitude_field(self):
        return self.settings.get("latitude_field")

    @property
    def longitude_field(self):
        return self.settings.get("longitude_field")

    @property
    def latlong_field(self):
        return self.settings.get("latlong_field")

    @property
    def coordinates_field_count(self):
        return self.settings.get("coordinates_field_count")

    @property
    def coordinates_separator(self):
        return self.settings.get("coordinates_separator")
