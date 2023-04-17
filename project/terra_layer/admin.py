from django.contrib import admin
from geostore.models import Feature
from geostore.models import Layer as GeostoreLayer
from model_clone import CloneModelAdmin

from project.terra_layer.models import Layer, Scene, StyleImage


class StyleImageInline(admin.TabularInline):
    model = StyleImage
    extra = 0
    readonly_fields = ("slug",)


class LayerAdmin(CloneModelAdmin):
    inlines = [
        StyleImageInline,
    ]
    list_display = ("name", "source")


admin.site.register(Layer, LayerAdmin)
admin.site.register(GeostoreLayer)


class FeatureAdmin(admin.ModelAdmin):
    list_display = ("id", "identifier", "layer")
    list_filter = ("layer",)


admin.site.register(Feature, FeatureAdmin)
admin.site.register(Scene)
