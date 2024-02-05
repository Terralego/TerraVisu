from django.contrib import admin

from project.geosource.models import (
    CommandSource,
    CSVSource,
    Field,
    GeoJSONSource,
    PostGISSource,
    ShapefileSource,
    WMTSSource,
)


class FieldInline(admin.TabularInline):
    model = Field
    extra = 0


class SourceAdmin(admin.ModelAdmin):
    inlines = [FieldInline]
    list_display = ("id", "name", "slug", "geom_type", "status")


admin.site.register(PostGISSource, SourceAdmin)
admin.site.register(GeoJSONSource, SourceAdmin)
admin.site.register(ShapefileSource, SourceAdmin)
admin.site.register(CommandSource, SourceAdmin)
admin.site.register(CSVSource, SourceAdmin)
admin.site.register(WMTSSource, SourceAdmin)
