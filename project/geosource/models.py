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
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSGeometry
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from fiona.crs import to_string
from geostore import GeometryTypes
from polymorphic.models import PolymorphicModel
from psycopg2 import sql
from pyproj import CRS

from .callbacks import get_attr_from_path
from .elasticsearch.index import LayerESIndex
from .exceptions import CSVSourceException, GeoJSONSourceException, SourceException
from .fields import LongURLField
from .mixins import CeleryCallMethodsMixin
from .signals import refresh_data_done

User = get_user_model()

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


class SourceReporting(models.Model):
    class Status(models.IntegerChoices):
        SUCCESS = 0, _("Success")
        ERROR = 1, _("Error")
        WARNING = 2, _("Warning")
        PENDING = 3, _("Pending")

    status = models.PositiveSmallIntegerField(
        choices=Status.choices, null=True, default=None
    )
    message = models.CharField(max_length=255, default="")
    started = models.DateTimeField(null=True)
    ended = models.DateTimeField(null=True)
    added_lines = models.PositiveIntegerField(default=0)
    deleted_lines = models.PositiveIntegerField(default=0)
    modified_lines = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list)

    def __str__(self):
        return f"{self.status}"

    def reset(self):
        self.message = ""
        self.started = None
        self.ended = None
        self.added_lines = 0
        self.deleted_lines = 0
        self.modified_lines = 0
        self.total = 0
        self.errors = []


class Source(PolymorphicModel, CeleryCallMethodsMixin):
    class Status(models.IntegerChoices):
        NEED_SYNC = 0, _("Need sync")
        PENDING = 1, _("Pending")
        DONE = 2, _("Done")
        IN_PROGRESS = 3, _("In progress")

    name = models.CharField(max_length=255, unique=True)
    credit = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    id_field = models.CharField(max_length=255, default="id")
    geom_type = models.IntegerField(
        choices=GeometryTypes.choices, null=True, blank=True
    )

    settings = models.JSONField(default=dict, blank=True)
    groups = models.ManyToManyField(Group, blank=True, related_name="geosources")
    report = models.OneToOneField(SourceReporting, on_delete=models.SET_NULL, null=True)

    task_id = models.CharField(null=False, max_length=255, blank=True, default="")
    task_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_refresh = models.DateTimeField(
        default=None, null=True, blank=True, db_index=True
    )
    status = models.PositiveSmallIntegerField(
        choices=Status.choices, default=Status.NEED_SYNC
    )
    author = models.ForeignKey(
        User, related_name="sources", blank=True, null=True, on_delete=models.SET_NULL
    )

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
        self.status = self.Status.IN_PROGRESS
        self.save()

        layer = self.get_layer()
        try:
            es_index = LayerESIndex(layer)
            es_index.index()
            response = self._refresh_data(es_index)
            self.status = self.Status.DONE.value
            return response

        except Exception as exc:
            self.report.status = self.report.Status.ERROR.value
            self.report.message = str(exc)
            self.report.ended = timezone.now()
            self.report.save(update_fields=["status", "message", "ended"])
            self.status = self.Status.DONE

        finally:
            self.last_refresh = timezone.now()
            self.save()
            refresh_data_done.send_robust(
                sender=self.__class__,
                layer=layer.pk,
            )

    def _refresh_data(self, es_index=None):
        if not self.report:
            self.report = SourceReporting.objects.create(started=timezone.now())
        else:
            self.report.reset()
            self.report.started = timezone.now()
            self.report.save()

        layer = self.get_layer()
        begin_date = timezone.now()
        row_count = 0
        added_rows = 0
        modified_rows = 0
        total = 0
        try:
            records, records_errors = self._get_records()
        except Exception as exc:
            # Possible Uncatched exception (i.e ValueError, Integer Error)
            raise SourceException(exc.args)

        self.report.errors += records_errors
        for i, row in enumerate(records):
            total += 1
            geometry = row.pop(self.SOURCE_GEOM_ATTRIBUTE)
            try:
                identifier = row[self.id_field]
                try:
                    sid = transaction.savepoint()
                    feature, created = self.update_feature(
                        layer, identifier, geometry, row
                    )
                    if es_index and feature:
                        es_index.index_feature(layer, feature)
                    transaction.savepoint_commit(sid)
                    if created:
                        added_rows += 1
                    else:
                        modified_rows += 1
                except Exception as exc:
                    transaction.savepoint_rollback(sid)
                    self.report.errors.append(f"{self.id_field} - {identifier}: {exc}")
                    continue
            except KeyError:
                self.report.errors.append(
                    f"Line {i} - Can't find identifier '{self.id_field}'"
                )
                continue
            row_count += 1
        deleted, _ = self.clear_features(layer, begin_date)

        self.report.added_lines = added_rows
        self.report.modified_lines = modified_rows
        self.report.deleted_lines = deleted
        self.report.total = row_count
        if not row_count:
            self.report.status = SourceReporting.Status.ERROR.value
            self.report.message = gettext("Failed to refresh data")
        elif row_count == total and len(self.report.errors) == 0:
            self.report.status = SourceReporting.Status.SUCCESS.value
            self.report.message = gettext("Source refreshed successfully")
        else:
            self.report.status = SourceReporting.Status.WARNING.value
            self.report.message = gettext("Source refreshed partially")
        if self.id:
            self.report.ended = timezone.now()
            self.report.save()
        return {"count": row_count, "total": total}

    @transaction.atomic
    def update_fields(self):
        records, _ = self._get_records(50)

        fields = {}
        if records is None:
            return {"count": 0}

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
        return f"{self.name} - ({self.slug})"

    @property
    def type(self):
        return self.__class__

    @property
    def refresh_status(self):
        return self.status


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

    class Meta:
        unique_together = ["source", "name"]
        ordering = ("order",)

    def __str__(self):
        return f"{self.name} ({self.source.name} - {self.data_type})"


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
            if not self.report:
                self.report = SourceReporting(started=timezone.now())
            self.report.status = SourceReporting.Status.ERROR.value
            self.report.errors.append(err.args[0])
            self.report.save()
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

        return (cursor, [])

    class Meta:
        verbose_name = _("PostGIS Source")
        verbose_name_plural = _("PostGIS Sources")


class GeoJSONSource(Source):
    file = models.FileField(upload_to="geosource/geojson/%Y/")

    def get_file_as_dict(self):
        try:
            return json.load(self.file)
        except json.JSONDecodeError:
            msg = "Source's GeoJSON file is not valid"
            raise GeoJSONSourceException(msg)

    def _get_records(self, limit=None):
        geojson = self.get_file_as_dict()

        limit = limit if limit else len(geojson["features"])

        records = []
        errors = []
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
            except (ValueError, GDALException) as exc:
                feature_id = record.get("properties", {}).get("id", i)
                errors.append(f"Feature id {feature_id}: {exc}")
        return (records, errors)

    class Meta:
        verbose_name = _("GeoJSON Source")
        verbose_name_plural = _("GeoJSON Sources")


class ShapefileSource(Source):
    # Zipped ShapeFile
    file = models.FileField(upload_to="geosource/shapefile/%Y/")

    def _get_records(self, limit=None):
        with fiona.BytesCollection(self.file.read()) as shapefile:
            limit = limit if limit else len(shapefile)
            # Detect the EPSG

            ccs = CRS(to_string(shapefile.crs))
            srid = ccs.to_epsg()
            if not srid:
                srid = 4326
            # Return geometries with a hack to set the correct geometry srid
            records = []
            for feature in shapefile[:limit]:
                geometry = GEOSGeometry(
                    json.dumps(
                        {
                            "type": feature.get("geometry").get("type"),
                            "coordinates": feature.get("geometry").get("coordinates"),
                        }
                    )
                )
                geometry.srid = srid
                records.append(
                    {
                        self.SOURCE_GEOM_ATTRIBUTE: geometry,
                        **feature.get("properties", {}),
                    }
                )

            # No errors caught for Shapefile
            return records, []

    class Meta:
        verbose_name = _("Shapefile Source")
        verbose_name_plural = _("Shapefile Sources")


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
        return [None, None]

    class Meta:
        verbose_name = _("Command Source")
        verbose_name_plural = _("Command Sources")


class WMTSSource(Source):
    minzoom = models.IntegerField(null=True)
    maxzoom = models.IntegerField(null=True)
    tile_size = models.IntegerField()
    url = LongURLField()

    @property
    def refresh_status(self):
        return None

    def get_status(self):
        return {"state": "DONT_NEED"}

    def refresh_data(self):
        return {}

    def _get_records(self, limit=None):
        return [None, None]

    class Meta:
        verbose_name = _("WMTS Source")
        verbose_name_plural = _("WMTS Sources")


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
        except (pyexcel.exceptions.FileTypeNotSupported, Exception):
            msg = "Provided CSV file is invalid"
            raise CSVSourceException(msg)

    def _get_records(self, limit=None):
        sheet = self.get_file_as_sheet()
        if self.settings.get("use_header"):
            sheet.name_columns_by_row(0)

        ignored_columns = []
        if self.settings.get("ignore_columns"):
            ignored_columns = self._get_null_columns_indexes(sheet)

        limit = limit if limit else len(sheet)

        records = []
        errors = []
        srid = self._get_srid()

        for i, row in enumerate(sheet):
            if self.settings["coordinates_field"] == "two_columns":
                lat_field = self.settings["latitude_field"]
                lng_field = self.settings["longitude_field"]

                try:
                    x, y = self._extract_coordinates(
                        row, sheet.colnames, [lng_field, lat_field]
                    )
                except CSVSourceException as e:
                    errors.append(f"Sheet row {i} - {e.message}")
                    continue

                ignored_field = (row.index(x), row.index(y), *ignored_columns)
            else:
                lnglat_field = self.settings["latlong_field"]
                try:
                    x, y = self._extract_coordinates(
                        row, sheet.colnames, [lnglat_field]
                    )
                except CSVSourceException as e:
                    errors.append(f"Sheet row {i} - {e.message}")
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
                errors.append(
                    f"Sheet row {i} - One of source's record has invalid geometry: Point({x} {y}) srid={srid}"
                )
                continue
        return (records, errors)

    def _extract_coordinates(self, row, colnames, coord_fields):
        coords = []
        for field in coord_fields:
            # if no header, we expect index for the columns has been provided
            try:
                field_index = (
                    colnames.index(field)
                    if self.settings.get("use_header")
                    else int(field)
                )
            except ValueError:
                msg = f"{field} is not a valid coordinate field"
                raise CSVSourceException(msg)

            c = row[field_index]
            coords.append(c)
        if len(coords) == 2:
            x, y = coords
        else:
            sep = self._get_separator(self.settings["coordinates_separator"])
            is_xy = self.settings["coordinates_field_count"] == "xy"
            try:
                # some fools use a reversed cartesian coordinates system (╯°□°)╯︵ ┻━┻
                x, y = coords[0].split(sep) if is_xy else coords[0].split(sep)[::-1]
            except ValueError:
                msg = f'Cannot split coordinate "{coords[0]}" with separator "{sep}"'
                raise CSVSourceException(msg)

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
        except (IndexError, ValueError):
            msg = f"Invalid SRID: {coordinate_reference_system}"
            raise CSVSourceException(msg)

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

    class Meta:
        verbose_name = _("CSV Source")
        verbose_name_plural = _("CSV Sources")
