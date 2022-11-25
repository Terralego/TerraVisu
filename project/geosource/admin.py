from django.contrib import admin

from project.geosource.models import (
    CommandSource,
    CSVSource,
    GeoJSONSource,
    PostGISSource,
    ShapefileSource,
    WMTSSource,
)

admin.site.register(PostGISSource)

admin.site.register(GeoJSONSource)

admin.site.register(ShapefileSource)

admin.site.register(CommandSource)

admin.site.register(WMTSSource)

admin.site.register(CSVSource)
