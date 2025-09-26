import csv
from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from geostore.models import Feature
from geostore.models import Layer as GeostoreLayer
from model_clone import CloneModelAdmin

from project.admin import config_site
from project.terra_layer.filters import MonthYearFilter
from project.terra_layer.models import (
    Declaration,
    DeclarationConfig,
    DeclarationField,
    Layer,
    Report,
    ReportConfig,
    ReportField,
    Scene,
    Status,
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


class ReportAndDeclarationDisplayMixin:
    """Mixin to add status change display functionality to ModelAdmin classes."""

    status_changes_field = None
    content_title_field = None
    content_value_field = None

    def display_status_changes(self, obj):
        status_changes = getattr(obj, self.status_changes_field).order_by("updated_at")

        content = ["<table>"]

        # Header row with dates
        content.append("<tr>")
        for status_change in status_changes:
            content.append(
                f"<th>{date_format(status_change.updated_at)} - {status_change.updated_at.time().strftime('%Hh%M')}</th>"
            )
        content.append("</tr>")

        # Status transition row
        content.append("<tr>")
        for status_change in status_changes:
            status_before = getattr(Status, status_change.status_before).label
            status_after = getattr(Status, status_change.status_after).label
            content.append(f"<td>{status_before} → {status_after}</td>")
        content.append("</tr>")

        # Message row
        content.append("<tr>")
        for status_change in status_changes:
            content.append(f"<td>{status_change.message or '-'}</td>")
        content.append("</tr>")

        content.append("</table>")
        return format_html("".join(content))

    display_status_changes.short_description = _("Status changes")

    def display_files(self, obj):
        files_links = []
        for file in obj.files.order_by("uploaded_at"):
            files_links.append(
                format_html(
                    '&#128196; <a href="{}">{}</a><br>',
                    "/" + file.file.url,
                    Path(file.file.name).name,
                )
            )
        return format_html("".join(files_links))

    display_files.short_description = _("Files")

    def display_content(self, obj):
        free_comment_string = _("Free comment")
        content = "<table>"
        content += "<tr>"
        for field in obj.content:
            content += (
                f"<th>{field.get(self.content_title_field, free_comment_string)}</th>"
            )
        content += "</tr>"
        content += "<tr>"
        for field in obj.content:
            content += f"<td>{field.get(self.content_value_field, field.get('free_comment'))}</td>"
        content += "</tr>"
        content += "</table>"
        return format_html("".join(content))

    display_content.short_description = _("Content")


@admin.register(Report)
class ReportAdmin(ReportAndDeclarationDisplayMixin, admin.ModelAdmin):
    list_display = (
        "display_id",
        "created_at",
        "status",
        "display_email",
        "display_layer",
    )
    status_changes_field = "report_status_changes"
    content_title_field = "label"
    content_value_field = "content"
    list_filter = ("status", MonthYearFilter)
    ordering = ["-created_at"]
    form = ReportAdminForm
    readonly_fields = (
        "config",
        "display_feature",
        "created_at",
        "display_email",
        "display_layer",
        "display_content",
        "display_files",
        "display_status_changes",
    )
    fields = (
        "config",
        "created_at",
        "display_email",
        "display_layer",
        "display_feature",
        "display_content",
        "geom",
        "display_files",
        "display_status_changes",
        "status",
        "managers_message",
    )
    exclude = ("config", "feature", "layer", "email", "user", "content")

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        # Only show geom if it has a value
        if obj and not obj.geom:
            fields.remove("geom")
        return fields

    def has_add_permission(self, request):
        # Creation through API only
        return False

    def display_layer(self, obj):
        return obj.layer.name

    display_layer.short_description = _("Layer")

    def display_id(self, obj):
        return f"{_('Report')} {obj.id}"

    display_id.short_description = _("Report")

    def display_email(self, obj):
        return obj.user.email if obj.user else _("Deleted user")

    display_email.short_description = _("Email")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset.prefetch_related("files", "declaration_status_changes").select_related(
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
    status_changes_field = "declaration_status_changes"
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


class DeclarationAdmin(ReportAndDeclarationDisplayMixin, admin.ModelAdmin):
    list_display = ("display_id", "created_at", "status", "display_email_list")
    list_filter = ("status", MonthYearFilter)
    status_changes_field = "declaration_status_changes"
    content_title_field = "title"
    content_value_field = "value"
    form = DeclarationAdminForm
    ordering = ["-created_at"]

    readonly_fields = (
        "created_at",
        "display_user",
        "display_email_detail",
        "display_content",
        "display_files",
        "display_status_changes",
    )
    # Reorder all fields including those from AdminForm
    fields = (
        "created_at",
        "display_user",
        "display_email_detail",
        "display_content",
        "geom",
        "display_files",
        "display_status_changes",
        "status",
        "managers_message",
    )
    exclude = ("user", "email", "content")
    actions = ["export_as_csv"]

    def has_add_permission(self, request):
        # Creation through API only
        return False

    def display_id(self, obj):
        return f"{_('Declaration')} {obj.id}"

    display_id.short_description = _("Declaration")

    def display_user(self, obj):
        return obj.user.email if obj.user else _("No user")

    display_user.short_description = _("User")

    def display_email_list(self, obj):
        return (
            obj.user.email
            if obj.user
            else obj.email
            if obj.email
            else _("Deleted email")
        )

    display_email_list.short_description = _("Email")

    def display_email_detail(self, obj):
        return obj.email if obj.email else _("See user")

    display_email_detail.short_description = _("Email")

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="declarations.csv"'
        scheme = "https" if settings.SSL_ENABLED else "http"
        server_name = request.get_host()
        writer = csv.writer(response)

        header = [
            _("ID"),
            _("Created at"),
            _("Status"),
            _("Email"),
            _("Latitude"),
            _("Longitude"),
            _("Content"),
            _("Files"),
            _("Status changes"),
        ]
        writer.writerow(header)

        for declaration in queryset.prefetch_related(
            "files", "declaration_status_changes"
        ).select_related("user"):
            email = (
                declaration.user.email
                if declaration.user
                else (declaration.email if declaration.email else _("Deleted email"))
            )

            latitude = declaration.geom.y if declaration.geom else ""
            longitude = declaration.geom.x if declaration.geom else ""

            content_fields = []
            if declaration.content:
                for field in declaration.content:
                    title = field.get("title", _("Free comment"))
                    value = field.get("value", field.get("free_comment", ""))
                    content_fields.append(f"{title}: {value}")
            content_str = " | ".join(content_fields)

            file_urls = []
            for declaration_file in declaration.files.all():
                full_file_url = f"{scheme}://{server_name}/{declaration_file.file.url}"
                file_urls.append(full_file_url)
            files_str = " | ".join(file_urls)

            status_changes_str = []
            for status_change in declaration.declaration_status_changes.all():
                status_before = getattr(Status, status_change.status_before).label
                status_after = getattr(Status, status_change.status_after).label
                status_changes_str.append(
                    f"{status_change.updated_at.strftime('%d/%m/%Y')} ({status_before} → {status_after}): {status_change.message}"
                )
            status_changes_str = " | ".join(status_changes_str)

            row = [
                declaration.pk,
                declaration.created_at.strftime("%d/%m/%Y %H:%M"),
                declaration.get_status_display(),
                email,
                latitude,
                longitude,
                content_str,
                files_str,
                status_changes_str,
            ]
            writer.writerow(row)

        return response

    export_as_csv.short_description = _("Export selected declarations as CSV")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset.prefetch_related("files", "declaration_status_changes").select_related(
            "status", "user"
        )
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
