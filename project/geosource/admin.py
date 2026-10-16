from django.contrib import admin

from project.geosource.models import (
    CommandSource,
    CSVSource,
    Field,
    GeoFileSource,
    PostGISSource,
    WMTSSource,
)


class FieldInline(admin.TabularInline):
    model = Field
    extra = 0


@admin.register(
    CSVSource,
    CommandSource,
    GeoFileSource,
    PostGISSource,
    WMTSSource,
)
class SourceAdmin(admin.ModelAdmin):
    inlines = [FieldInline]
    list_display = ("id", "name", "slug", "geom_type", "status")
