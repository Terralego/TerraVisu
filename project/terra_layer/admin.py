from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from geostore.models import Feature
from geostore.models import Layer as GeostoreLayer
from model_clone import CloneModelAdmin

from project.terra_layer.models import Layer, Scene, StyleImage


class StyleImageInline(admin.TabularInline):
    model = StyleImage
    extra = 0
    readonly_fields = ("slug",)


@admin.register(Layer)
class LayerAdmin(CloneModelAdmin):
    inlines = [
        StyleImageInline,
    ]
    list_display = ("id", "name", "source", "layer_identifier", "uuid")
    list_filter = ("source",)
    search_fields = ("name", "layer_identifier", "id", "uuid")
    readonly_fields = ("layer_identifier",)

    @admin.display(
        description=_("Layer identifier"),
        ordering="layer_identifier",
    )
    def layer_identifier(self, obj):
        return obj.layer_identifier


admin.site.register(GeostoreLayer)


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("id", "identifier", "layer")
    list_filter = ("layer",)


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "category", "custom_icon", "order")
    list_filter = ("category",)
    search_fields = ("id", "name", "slug")
