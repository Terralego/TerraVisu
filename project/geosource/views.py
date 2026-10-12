import csv
import json
import logging
import mimetypes
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from zipfile import is_zipfile

from django.contrib.gis.gdal import (
    CoordTransform,
    DataSource,
    OGRGeometry,
    SpatialReference,
)
from django.contrib.gis.gdal.geometries import Point
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.db.models import Count
from django.http import Http404
from geostore import GeometryTypes
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import SourceFilterSet
from .models import (
    FieldTypes,
    Source,
    SourceReporting,
    detect_boolean_fields,
    open_zipped_shapefile_layer,
)
from .parsers import NestedMultipartJSONParser
from .permissions import SourcePermission
from .serializers import SourceListSerializer, SourceSerializer, strip_storage_suffix

logger = logging.getLogger(__name__)

OFT_NAME_MAP = {
    "OFTInteger": "int",
    "OFTInteger64": "int",
    "OFTReal": "float",
    "OFTString": "str",
    "OFTDate": "date",
    "OFTTime": "time",
    "OFTDateTime": "datetime",
    "OFTBinary": "bytes",
    "OFTIntegerList": "list",
    "OFTRealList": "list",
    "OFTStringList": "list",
}


@contextmanager
def uploaded_file_path(uploaded_file):
    """Yield a filesystem path for an uploaded file, reusing Django's
    temporary upload file when already on disk."""
    if isinstance(uploaded_file, TemporaryUploadedFile):
        yield uploaded_file.temporary_file_path()
    else:
        suffix = os.path.splitext(uploaded_file.name)[1]
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(uploaded_file.read())
        tmp.close()
        try:
            yield tmp.name
        finally:
            os.unlink(tmp.name)


def _geom_type_id(geom_type_name):
    if geom_type_name in GeometryTypes.__members__:
        return GeometryTypes[geom_type_name].value
    return None


_OGR_GEOMETRY_TO_NAME = {name.upper(): name for name in GeometryTypes.__members__}


def _detect_geometry_types(file_path, layer_name):
    sql = f'SELECT DISTINCT OGR_GEOMETRY FROM "{layer_name}"'
    try:
        result = subprocess.run(
            [
                "ogrinfo", "-json", "-al", "-features", "-geom=NO",
                "-dialect", "OGRSQL", "-sql", sql, file_path,
            ],
            capture_output=True, text=True, timeout=60, check=True,
        )
        data = json.loads(result.stdout)
        layers = data.get("layers") or []
        raw_values = {
            feat.get("properties", {}).get("OGR_GEOMETRY")
            for feat in (layers[0].get("features", []) if layers else [])
        }
        return {
            _OGR_GEOMETRY_TO_NAME.get(v.upper(), v.title())
            for v in raw_values if v
        }
    except (subprocess.SubprocessError, ValueError, KeyError, IndexError) as exc:
        logger.warning("ogrinfo geometry-type detection failed for %s: %s", file_path, exc)
        return set()


_GEOJSON_GEOM_TYPE_RE = re.compile(
    rb'"geometry"\s*:\s*\{\s*"type"\s*:\s*"'
    rb'(Point|MultiPoint|LineString|MultiLineString|Polygon|MultiPolygon|GeometryCollection)"'
)


def _detect_geojson_geometry_types(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return {m.decode() for m in _GEOJSON_GEOM_TYPE_RE.findall(data)}
    except OSError as exc:
        logger.warning("regex geometry-type detection failed for %s: %s", file_path, exc)
        return set()


def _preview_bool_fields(layer, features, file_path, is_gpkg):
    if is_gpkg and file_path:
        return detect_boolean_fields(file_path, layer.name)

    bool_fields = set()
    for fn, ft in zip(layer.fields, layer.field_types):
        if ft.__name__ in ("OFTInteger", "OFTInteger64"):
            vals = [row[fn] for row in features if fn in row and row[fn] is not None]
            if vals and 0 in vals and 1 in vals and all(v in (0, 1, True, False) for v in vals):
                bool_fields.add(fn)
    return bool_fields


class SourceModelViewset(ModelViewSet):
    parser_classes = (JSONParser, NestedMultipartJSONParser)
    permission_classes = (SourcePermission,)
    filterset_class = SourceFilterSet
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return SourceListSerializer
        return SourceSerializer

    def get_queryset(self):
        qs = Source.objects.all().order_by("-id")
        if self.action == "list":
            # used to filter by layers count
            qs = qs.annotate(layers_count=Count("layers"))
        return qs

    def perform_create(self, serializers):
        serializers.save(author=self.request.user)

    def _list_gpkg_layers(self, ds):
        return [
            {
                "name": ds[i].name,
                "geom_type": ds[i].geom_type.name if ds[i].geom_type else "Unknown",
            }
            for i in range(ds.layer_count)
        ]

    def _preview_ogr(self, file_path, layer_name="", is_geojson=False, is_gpkg=False):
        ds = DataSource(file_path)

        if is_gpkg:
            available = [info["name"] for info in self._list_gpkg_layers(ds)]
            if layer_name and layer_name in available:
                layer = ds[layer_name]
            else:
                layer = ds[0]
        else:
            layer = ds[0]

        return self._extract_layer_data(
            layer, file_path=file_path,
            is_geojson=is_geojson, is_gpkg=is_gpkg,
        )

    def _preview_shapefile(self, file_path):
        if is_zipfile(file_path):
            with open_zipped_shapefile_layer(file_path) as layer:
                if layer is None:
                    error_msg = "No .shp file found in archive"
                    raise ValueError(error_msg)
                return self._extract_layer_data(layer)

        ds = DataSource(file_path)
        return self._extract_layer_data(ds[0])

    def _preview_csv(
        self, file_path,
        field_separator="semicolon",
        char_delimiter="doublequote",
        decimal_separator="point",
        encoding="UTF-8",
        number_lines_to_ignore=0,
        use_header=True,
        coordinates_field=None,
        latitude_field=None,
        longitude_field=None,
        latlong_field=None,
        coordinates_field_count=None,
        coordinates_separator=None,
        coordinate_reference_system=None,
    ):
        SEP_MAP = {
            "comma": ",", "semicolon": ";", "tab": "\t", "tabulation": "\t",
            "colon": ":", "space": " ", "point": ".",
            "doublequote": '"', "simplequote": "'",
        }
        delimiter = SEP_MAP.get(field_separator, field_separator)
        quotechar = SEP_MAP.get(char_delimiter, char_delimiter)
        decimal_sep = SEP_MAP.get(decimal_separator, decimal_separator)

        result = {
            "record_count": 0,
            "geometry_type": None, "geometry_type_name": None,
            "geometry_types": None, "mixed_geometries": False,
            "crs": None, "fields": [], "features": [],
            "bbox": None, "column_count": 0,
        }

        with open(file_path, encoding=encoding, errors="replace", newline="") as fh:
            for _ in range(number_lines_to_ignore):
                fh.readline()

            reader = csv.reader(fh, delimiter=delimiter, quotechar=quotechar)
            try:
                first_row = next(reader)
            except StopIteration:
                return result

            if use_header:
                headers = first_row
            else:
                headers = [f"Col_{i+1}" for i in range(len(first_row))]

            srid = None
            if coordinate_reference_system:
                try:
                    srid = int(coordinate_reference_system.split("_")[1])
                except (ValueError, IndexError):
                    srid = None

            coord_indexes = None
            is_xy = True
            one_column_sep = None
            if coordinates_field == "two_columns" and latitude_field and longitude_field:
                try:
                    lat_idx = headers.index(latitude_field) if use_header else int(latitude_field)
                    lng_idx = headers.index(longitude_field) if use_header else int(longitude_field)
                    coord_indexes = (lng_idx, lat_idx)
                except (ValueError, TypeError):
                    coord_indexes = None
            elif (
                coordinates_field == "one_column"
                and latlong_field and coordinates_field_count and coordinates_separator
            ):
                try:
                    col_idx = headers.index(latlong_field) if use_header else int(latlong_field)
                except (ValueError, TypeError):
                    col_idx = None
                if col_idx is not None:
                    coord_indexes = (col_idx,)
                    is_xy = coordinates_field_count == "xy"
                    one_column_sep = SEP_MAP.get(coordinates_separator, coordinates_separator)

            def extract_xy(row):
                if coord_indexes is None:
                    return None
                try:
                    if len(coord_indexes) == 2:
                        x_val = row[coord_indexes[0]]
                        y_val = row[coord_indexes[1]]
                    else:
                        parts = row[coord_indexes[0]].split(one_column_sep)
                        if is_xy:
                            x_val, y_val = parts[0], parts[1]
                        else:
                            x_val, y_val = parts[1], parts[0]
                except (IndexError, ValueError):
                    return None
                if decimal_sep != ".":
                    x_val = x_val.replace(decimal_sep, ".")
                    y_val = y_val.replace(decimal_sep, ".")
                try:
                    return float(x_val), float(y_val)
                except (ValueError, TypeError):
                    return None

            data_rows = []
            record_count = 0
            minx = miny = float("inf")
            maxx = maxy = float("-inf")
            found_coord = False

            def iter_rows():
                if not use_header:
                    yield first_row
                yield from reader

            for row in iter_rows():
                if len(data_rows) < 5:
                    data_rows.append(row)
                record_count += 1
                if coord_indexes is not None:
                    xy = extract_xy(row)
                    if xy:
                        found_coord = True
                        x, y = xy
                        minx = min(minx, x)
                        miny = min(miny, y)
                        maxx = max(maxx, x)
                        maxy = max(maxy, y)

        def detect_type(values):
            if not values:
                return "str"
            if all(v.lstrip("-").isdigit() for v in values):
                return "int"
            try:
                [float(v.replace(decimal_sep, ".")) for v in values]
                if decimal_sep != ".":
                    if not any(decimal_sep in v for v in values) and any("." in v for v in values):
                        return "str"
                return "float"
            except ValueError:
                pass
            if all(v.lower() in ("true", "false", "0", "1") for v in values):
                return "boolean"
            return "str"

        fields = []
        for i, col in enumerate(headers):
            col_values = [
                row[i] for row in data_rows
                if i < len(row) and row[i] != ""
            ]
            fields.append({"name": col, "type": detect_type(col_values)})

        features = [
            {h: (v if v != "" else None) for h, v in zip(headers, row)}
            for row in data_rows
        ]

        bbox = None
        if found_coord:
            if srid and srid != 4326:
                ct = CoordTransform(SpatialReference(srid), SpatialReference(4326))
                xs = []
                ys = []
                for cx, cy in ((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)):
                    pt = Point(f"POINT({cx} {cy})")
                    pt.transform(ct)
                    xs.append(pt.x)
                    ys.append(pt.y)
                bbox = [min(xs), min(ys), max(xs), max(ys)]
            else:
                bbox = [minx, miny, maxx, maxy]

        result.update({
            "record_count": record_count,
            "crs": f"EPSG:{srid}" if srid else None,
            "fields": fields,
            "features": features,
            "bbox": bbox,
            "column_count": len(headers),
        })
        return result

    def _extract_layer_data(self, layer, file_path=None, is_geojson=False, is_gpkg=False):
        features = []
        for feature in layer:
            if len(features) >= 5:
                break
            features.append({fn: feature.get(fn) for fn in feature.fields})

        bool_fields = _preview_bool_fields(layer, features, file_path, is_gpkg)

        fields = [
            {
                "name": fn,
                "type": "boolean" if fn in bool_fields else OFT_NAME_MAP.get(ft.__name__, ft.__name__),
            }
            for fn, ft in zip(layer.fields, layer.field_types)
        ]

        for row in features:
            for fn in bool_fields:
                if fn in row:
                    row[fn] = bool(row[fn])

        geom_type_name = layer.geom_type.name if layer.geom_type else None
        geom_type = _geom_type_id(geom_type_name)

        geometry_types = None
        mixed_geometries = False
        if geom_type_name in (None, "Unknown") and file_path:
            if is_geojson:
                seen_types = _detect_geojson_geometry_types(file_path)
            else:
                seen_types = _detect_geometry_types(file_path, layer.name)
            if len(seen_types) == 1:
                geom_type_name = seen_types.pop()
                geom_type = _geom_type_id(geom_type_name)
            elif len(seen_types) > 1:
                geometry_types = sorted(seen_types)
                mixed_geometries = True

        crs_str = None
        if layer.srs:
            srid = layer.srs.srid
            crs_str = f"EPSG:{srid}" if srid else None

        bbox = None
        if layer.extent:
            extent = layer.extent
            if layer.srs and layer.srs.srid and layer.srs.srid != 4326:
                ct = CoordTransform(layer.srs, SpatialReference(4326))
                ring = OGRGeometry.from_bbox([extent.min_x, extent.min_y, extent.max_x, extent.max_y])
                ring.transform(ct)
                env = ring.extent
                bbox = [env[0], env[1], env[2], env[3]]
            else:
                bbox = [extent.min_x, extent.min_y, extent.max_x, extent.max_y]

        return {
            "record_count": layer.num_feat,
            "geometry_type": geom_type,
            "geometry_type_name": geom_type_name,
            "geometry_types": geometry_types,
            "mixed_geometries": mixed_geometries,
            "crs": crs_str,
            "fields": fields,
            "features": features,
            "bbox": bbox,
            "column_count": len(layer.fields),
        }

    @action(detail=True, methods=["get"])
    def refresh(self, request, pk):
        """Schedule a refresh now"""

        source = self.get_object()

        force_refresh = request.query_params.get("force")

        refresh_job = source.run_async_method("refresh_data", force=force_refresh)
        if refresh_job:
            source.status = Source.Status.PENDING.value
            if not source.report:
                source.report = SourceReporting.objects.create()
            source.save()
            return Response(
                data=source.get_status(),
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"])
    def property_values(self, request, pk):
        """
        Returns all distinct values of specified GET "property" params from
        database for the specified source layer.

        Note: if some record has no value for this property, None is contained in the
        result list.
        """
        property_to_list = request.query_params.get("property")
        if not property_to_list:
            return Response(
                {"error": 'Invalid "property" GET parameter'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source = self.get_object()
        result = source.get_layer().get_property_values(property_to_list)

        return Response(result)

    @action(detail=False, methods=["post"], url_path="gpkg-layers")
    def gpkg_layers(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with uploaded_file_path(uploaded_file) as file_path:
                ds = DataSource(file_path)
                layers = self._list_gpkg_layers(ds)
        except Exception as e:
            return Response(
                {"error": f"Invalid GPKG file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"layers": layers})

    @action(detail=False, methods=["post"], url_path="file-preview")
    def file_preview(self, request):
        uploaded_file = request.FILES.get("file")
        layer_name = request.data.get("layer_name", "")

        if not uploaded_file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = uploaded_file.name.lower()
        file_size = uploaded_file.size

        try:
            with uploaded_file_path(uploaded_file) as file_path:
                if filename.endswith(".gpkg"):
                    result = self._preview_ogr(file_path, layer_name=layer_name, is_gpkg=True)
                elif filename.endswith(".zip") or filename.endswith(".shp"):
                    result = self._preview_shapefile(file_path)
                elif filename.endswith(".geojson") or filename.endswith(".json"):
                    result = self._preview_ogr(file_path, is_geojson=True)
                elif filename.endswith(".csv"):
                    result = self._preview_csv(
                        file_path,
                        field_separator=request.data.get("field_separator", "semicolon"),
                        char_delimiter=request.data.get("char_delimiter", "doublequote"),
                        decimal_separator=request.data.get("decimal_separator", "point"),
                        encoding=request.data.get("encoding", "UTF-8"),
                        number_lines_to_ignore=int(request.data.get("number_lines_to_ignore", 0)),
                        use_header=request.data.get("use_header", "true") in ("true", "True", True),
                        coordinates_field=request.data.get("coordinates_field"),
                        latitude_field=request.data.get("latitude_field"),
                        longitude_field=request.data.get("longitude_field"),
                        latlong_field=request.data.get("latlong_field"),
                        coordinates_field_count=request.data.get("coordinates_field_count"),
                        coordinates_separator=request.data.get("coordinates_separator"),
                        coordinate_reference_system=request.data.get("coordinate_reference_system"),
                    )
                else:
                    return Response(
                        {"error": f"Unsupported file type: {filename}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except Exception as e:
            return Response(
                {"error": f"Failed to read file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result["file_size"] = file_size
        return Response(result)

    @action(detail=True, methods=["get"], url_path="file-preview")
    def file_preview_saved(self, request, pk=None):
        source = self.get_object()
        fields_qs = source.fields.order_by("order")

        type_map = {
            FieldTypes.String.value: "str",
            FieldTypes.Integer.value: "int",
            FieldTypes.Float.value: "float",
            FieldTypes.Boolean.value: "boolean",
            FieldTypes.Date.value: "date",
        }

        fields = []
        all_samples = {}
        for f in fields_qs:
            ft = type_map.get(f.data_type)
            if not ft:
                continue
            fields.append({"name": f.name, "type": ft})
            all_samples[f.name] = f.sample[:5] if f.sample else []

        features = [
            dict(zip(all_samples.keys(), row))
            for row in zip(*all_samples.values())
        ]

        record_count = 0
        if source.report:
            record_count = source.report.added_lines or 0

        file_field = getattr(source, "file", None)
        file_size = file_field.size if file_field else None

        geom_name = None
        geom_id = None
        if source.geom_type is not None:
            geom_name = GeometryTypes(source.geom_type).name
            geom_id = source.geom_type

        crs = "EPSG:4326"
        if source.original_srid and source.original_srid != 4326:
            crs = f"EPSG:4326 (original : EPSG:{source.original_srid})"

        bbox = None
        column_count = len(fields)

        if source.geom_type is not None:
            try:
                extent = source.get_layer().get_extent(srid=4326)["extent"]
                if extent:
                    bbox = list(extent)
            except Exception:
                logger.warning("bbox query failed for source %s", pk)

        if bbox is None and file_field:
            try:
                ds = DataSource(file_field.path)
                layer = ds[0]
                if layer.extent:
                    ext = layer.extent
                    if layer.srs and layer.srs.srid and layer.srs.srid != 4326:
                        ct = CoordTransform(layer.srs, SpatialReference(4326))
                        ring = OGRGeometry.from_bbox([ext.min_x, ext.min_y, ext.max_x, ext.max_y])
                        ring.transform(ct)
                        bbox = list(ring.extent)
                    else:
                        bbox = [ext.min_x, ext.min_y, ext.max_x, ext.max_y]
            except Exception:
                logger.warning("file-based bbox fallback failed for source %s", pk)

        geometry_types = None
        mixed_geometries = False
        if geom_name:
            geometry_types = [geom_name]

        return Response({
            "record_count": record_count,
            "geometry_type": geom_id,
            "geometry_type_name": geom_name,
            "geometry_types": geometry_types,
            "mixed_geometries": mixed_geometries,
            "crs": crs,
            "fields": fields,
            "features": features,
            "file_size": file_size,
            "bbox": bbox,
            "column_count": column_count,
        })

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download the uploaded source file."""
        from django.http import FileResponse

        source = self.get_object()
        file_field = getattr(source, "file", None)
        if not file_field:
            raise Http404("No file associated with this source")
        filename = strip_storage_suffix(os.path.basename(file_field.name))
        content_type, _ = mimetypes.guess_type(filename)
        return FileResponse(
            file_field.open("rb"),
            as_attachment=True,
            filename=filename,
            content_type=content_type,
        )

