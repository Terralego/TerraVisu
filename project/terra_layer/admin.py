from pathlib import Path

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from geostore.models import Feature
from geostore.models import Layer as GeostoreLayer
from model_clone import CloneModelAdmin

from project.admin import config_site
from project.terra_layer.models import (
    Declaration,
    DeclarationConfig,
    DeclarationField,
    Layer,
    Report,
    ReportConfig,
    ReportField,
    Scene,
    StyleImage,
)
from project.terra_layer.views.forms import DeclarationAdminForm, ReportAdminForm


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


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "display_email", "display_layer")
    list_filter = ("status",)
    readonly_fields = (
        "config",
        "display_feature",
        "created_at",
        "display_email",
        "display_layer",
        "display_content",
        "display_files",
    )
    fields = (
        "config",
        "created_at",
        "display_email",
        "display_layer",
        "display_feature",
        "display_content",
        "display_files",
        "status",
        "administrators_message",
    )
    form = ReportAdminForm
    exclude = ("config", "feature", "layer", "email", "user", "content")

    def has_add_permission(self, request):
        # Creation through API only
        return False

    def display_layer(self, obj):
        return obj.config.layer.name

    display_layer.short_description = _("Layer")

    def display_email(self, obj):
        return obj.user.email if obj.user else _("Deleted user")

    display_email.short_description = _("Email")

    def display_files(self, obj):
        files_links = []
        for report_file in obj.files.all():
            files_links.append(
                format_html(
                    '&#128196; <a href="{}">{}</a><br>',
                    "/" + report_file.file.url,
                    Path(report_file.file.name).name,
                )
            )
        return format_html("".join(files_links))

    display_files.short_description = _("Files")

    def display_content(self, obj):
        free_comment_string = _("Free comment")
        content = "<table>"
        content += "<tr>"
        for field in obj.content:
            content += f"<th>{field.get('label', free_comment_string)}</th>"
        content += "</tr>"
        content += "<tr>"
        for field in obj.content:
            content += f"<td>{field.get('content', field.get('free_comment'))}</td>"
        content += "</tr>"
        content += "</table>"
        return format_html("".join(content))

    display_content.short_description = _("Content")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset.prefetch_related("files").select_related(
            "status", "config", "config__layer", "user"
        )
        return queryset

    def display_feature(self, obj):
        main_field = getattr(obj.layer.main_field, "name", None)
        return (
            obj.feature.properties.get(main_field, None)
            if main_field
            else obj.feature.pk
        )

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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset.select_related("layer")
        return queryset


@admin.register(ReportField)
class ReportFieldAdmin(admin.ModelAdmin):
    list_display = ("display_field", "config", "order", "display_layer", "required")
    list_filter = ("config",)

    def display_layer(self, obj):
        return obj.config.layer.name

    display_layer.short_description = _("Layer")

    def display_field(self, obj):
        return obj.field.label

    display_field.short_description = _("Field")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("config", "config__layer", "field").order_by(
            "config", "order"
        )
        return queryset


config_site.register(Report, ReportAdmin)


class DeclarationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "display_email_list")
    list_filter = ("status",)
    form = DeclarationAdminForm
    readonly_fields = (
        "created_at",
        "display_user",
        "display_email_detail",
        "display_content",
        "display_files",
    )
    # Reorder all fields including those from AdminForm
    fields = (
        "created_at",
        "display_user",
        "display_email_detail",
        "display_content",
        "geom",
        "display_files",
        "status",
        "administrators_message",
    )
    exclude = ("user", "email", "content")

    def has_add_permission(self, request):
        # Creation through API only
        return False

    def display_user(self, obj):
        return obj.user.email if obj.user else _("No user")

    display_user.short_description = _("User")

    def display_email_list(self, obj):
        return obj.user.email if obj.user else obj.email

    display_email_list.short_description = _("Email")

    def display_email_detail(self, obj):
        return obj.email if obj.email else _("See user")

    display_email_detail.short_description = _("Email")

    def display_files(self, obj):
        files_links = []
        for declaration_file in obj.files.all():
            files_links.append(
                format_html(
                    '&#128196; <a href="{}">{}</a><br>',
                    "/" + declaration_file.file.url,
                    Path(declaration_file.file.name).name,
                )
            )
        return format_html("".join(files_links))

    display_files.short_description = _("Files")

    def display_content(self, obj):
        free_comment_string = _("Free comment")
        content = "<table>"
        content += "<tr>"
        for field in obj.content:
            content += f"<th>{field.get('title', free_comment_string)}</th>"
        content += "</tr>"
        content += "<tr>"
        for field in obj.content:
            content += f"<td>{field.get('value', field.get('free_comment'))}</td>"
        content += "</tr>"
        content += "</table>"
        return format_html("".join(content))

    display_content.short_description = _("Content")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset.prefetch_related("files").select_related("status", "user")
        return queryset


config_site.register(Declaration, DeclarationAdmin)


class DeclarationFieldInline(admin.TabularInline):
    model = DeclarationField
    fields = (
        "title",
        "helptext",
    )
    extra = 1


class DeclarationConfigAdmin(admin.ModelAdmin):
    list_display = ("title",)
    inlines = [DeclarationFieldInline]

    def has_add_permission(self, request):
        # There can be only one config
        perms = super().has_add_permission(request)
        if perms and DeclarationField.objects.exists():
            perms = False  # Disallow creating a new config if there is one already
        return perms


config_site.register(DeclarationConfig, DeclarationConfigAdmin)
