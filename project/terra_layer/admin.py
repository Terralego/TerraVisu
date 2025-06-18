from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from geostore.models import Feature
from geostore.models import Layer as GeostoreLayer
from model_clone import CloneModelAdmin

from project.terra_layer.models import (
    Layer,
    Report,
    ReportConfig,
    ReportField,
    ReportStatus,
    Scene,
    StyleImage,
)


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


@admin.register(ReportStatus)
class ReportStatusAdmin(admin.ModelAdmin):
    list_display = ("label",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "display_email", "display_layer")
    readonly_fields = (
        "display_feature",
        "created_at",
        "display_email",
        "display_layer",
        "content",
    )
    exclude = ("feature", "layer", "email", "user")

    def display_layer(self, obj):
        return obj.layer.name

    display_layer.short_description = _("Layer")

    def display_email(self, obj):
        return obj.get_email()

    display_email.short_description = _("Email")

    def display_feature(self, obj):
        main_field = getattr(obj.layer.main_field, "name", None)
        if main_field:
            return obj.feature.properties.get(main_field, None)
        return None

    display_feature.short_description = _("Feature")


@admin.register(ReportConfig)
class ReportConfigAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "display_layer",
    )
    readonly_fields = ("fields",)

    def display_layer(self, obj):
        return obj.layer.name

    display_layer.short_description = _("Layer")


@admin.register(ReportField)
class ReportFieldAdmin(admin.ModelAdmin):
    list_display = (
        "display_field",
        "config",
        "order",
        "display_layer",
    )
    list_filter = ("config",)

    def display_layer(self, obj):
        return obj.config.layer.name

    display_layer.short_description = _("Layer")

    def display_field(self, obj):
        return obj.field.label

    display_field.short_description = _("Field")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.order_by("config", "order")
        return queryset
