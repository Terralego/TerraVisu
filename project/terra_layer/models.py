import json
import uuid
from hashlib import md5

from autoslug import AutoSlugField
from django.db import models, transaction
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.generic.dates import timezone_today
from mapbox_baselayer.models import MapBaseLayer
from model_clone import CloneMixin
from rest_framework.reverse import reverse

from project.geosource.models import Field, Source

from .schema import SCENE_LAYERTREE, JSONSchemaValidator
from .style import generate_style_from_wizard


def scene_icon_path(instance, filename):
    y, m, d = timezone_today().isoformat().split("-")
    return f"terra_layer/scenes/custom_icon/{y}/{m}/{d}/{filename}"


class Scene(models.Model):
    """A scene is a group of data visualisation in terra-visu.
    It's also a main menu entry.
    """

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.CharField(max_length=255, default="map")
    custom_icon = models.ImageField(
        max_length=255, upload_to=scene_icon_path, null=True, default=None
    )
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    tree = models.JSONField(
        default=list,
        validators=[JSONSchemaValidator(limit_value=SCENE_LAYERTREE)],
    )
    config = models.JSONField(default=dict)
    base_layers = models.ManyToManyField(
        MapBaseLayer,
        blank=True,
        help_text="If no base layer defined, all base layers will be available.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("scene-detail", args=[self.pk])

    def tree2models(self, current_node=None, parent=None, order=0):
        """
        Generate groups structure from admin layer tree.
        This is a recursive function to handle each step of process.

        :param current_node: current node of the tree
        :param parent: The parent group of current node
        :param order: Current order to keep initial json order
        :returns: Nothing
        """

        # Init case, we've just launch the process
        if current_node is None:
            current_node = self.tree
            self.layer_groups.all().delete()  # Clear all groups to generate brand new one

        if not parent:
            # Create a default unique parent group that is ignored at export
            parent = LayerGroup.objects.create(view=self, label="Root")

        if isinstance(current_node, list):
            for idx, child in enumerate(current_node):
                self.tree2models(current_node=child, parent=parent, order=idx)

        elif "group" in current_node:
            # Handle groups
            group = parent.children.create(
                view=self,
                label=current_node["label"],
                exclusive=current_node.get("exclusive", False),
                selectors=current_node.get("selectors"),
                settings=current_node.get("settings", {}),
                order=order,
            )

            if "children" in current_node:
                self.tree2models(current_node=current_node["children"], parent=group)

        elif "geolayer" in current_node:
            # Handle layers
            layer = Layer.objects.get(pk=current_node["geolayer"])
            layer.group = parent
            layer.order = order
            layer.save(wizard_update=False)

    def insert_in_tree(self, layer, parts, group_config=None):
        """Add the layer in tree. Each parts are a group name to find inside the tree.
        Here we assume that missing groups are added at first position of current node
        We create missing group with default exclusive group configuration (should be corrected later if necessary)
        """
        group_config = group_config or {}

        current_node = self.tree
        last_group = None
        for part in parts:
            found = False
            # Search in groups
            for group in current_node:
                if group.get("group") and group["label"] == part:
                    last_group = group
                    current_node = group["children"]
                    found = True
                    break
            if not found:
                # Add the missing group part
                new_group = {"group": True, "label": part, "children": []}
                current_node.append(new_group)
                last_group = new_group
                current_node = new_group["children"]

        # Node if found (or created) we can add the geolayer now
        current_node.append({"geolayer": layer.id, "label": layer.name})

        if group_config and last_group:
            # And update tho config
            last_group.update(group_config)
        self.save()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)
        self.tree2models()  # Generate LayerGroups according to the tree

    @property
    def layers(self):
        """all scene layers"""
        return Layer.objects.filter(group__view=self).order_by("group__order", "order")

    @classmethod
    def get_user_scenes(cls, user):
        """Return all scenes that the user can access"""
        pks = []
        for scene in cls.objects.all():
            scene_layers = scene.layers.select_related("source")
            for layer in scene_layers:
                groups = layer.source.groups.all()
                if len(groups) == 0:
                    pks.append(scene.pk)
                elif user.is_authenticated:
                    if (
                        user.has_terra_perm("can_manage_layers")
                        or groups.intersection(user.groups.all()).exists()
                    ):
                        pks.append(scene.pk)
        return cls.objects.filter(pk__in=pks)

    class Meta:
        ordering = ["order"]


class LayerGroup(models.Model):
    view = models.ForeignKey(
        Scene, on_delete=models.CASCADE, related_name="layer_groups"
    )
    label = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self", null=True, on_delete=models.CASCADE, related_name="children"
    )
    order = models.IntegerField(default=0)
    exclusive = models.BooleanField(default=False)
    selectors = models.JSONField(null=True, default=None)
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]


class Layer(CloneMixin, models.Model):
    _clone_m2o_or_o2m_fields = ["style_images", "extra_styles"]
    _clone_excluded_fields = ["group"]  # don't include clone in group / scene
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="layers")
    group = models.ForeignKey(
        LayerGroup,
        on_delete=models.SET_NULL,
        null=True,
        related_name="layers",
        blank=True,
    )
    name = models.CharField(max_length=255, blank=False)
    in_tree = models.BooleanField(
        default=True, help_text="Whether the layer is shown in tree or hidden"
    )
    order = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    source_filter = models.TextField(
        blank=True, help_text="Contains the filter expression for source data"
    )
    layer_style = models.JSONField(default=dict, blank=True)  # To be removed
    layer_style_wizard = models.JSONField(default=dict, blank=True)  # To be removed
    main_style = models.JSONField(default=dict, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    active_by_default = models.BooleanField(default=False)
    legends = models.JSONField(default=list, blank=True)
    table_enable = models.BooleanField(default=False)
    table_export_enable = models.BooleanField(default=False)
    popup_config = models.JSONField(default=dict, blank=True)
    minisheet_config = models.JSONField(default=dict, blank=True)
    main_field = models.ForeignKey(
        Field,
        null=True,
        on_delete=models.SET_NULL,
        related_name="is_main_of",
        blank=True,
    )
    interactions = models.JSONField(default=list, blank=True)
    fields = models.ManyToManyField(Field, through="FilterField")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def map_style(self):
        return self.main_style.get("map_style", self.main_style)

    @cached_property
    def layer_identifier(self):
        return md5(f"{self.source.slug}-{self.pk}".encode("utf-8")).hexdigest()

    class Meta:
        ordering = ("order", "name")

    def generate_style_and_legend(self, style_config):
        # Add uid to style if missing
        if style_config and "uid" not in style_config:
            style_config["uid"] = str(uuid.uuid4())

        if style_config.get("type") == "wizard":
            generated_map_style, legend_additions = generate_style_from_wizard(
                self.source.get_layer(), style_config
            )
            style_config["map_style"] = generated_map_style
            return legend_additions

        return []

    def save(self, wizard_update=True, preserve_legend=False, **kwargs):
        super().save(**kwargs)

        if wizard_update:
            style_by_uid = {}
            # Mark not updated auto legends
            [
                legend.update({"not_updated": True})
                for legend in self.legends
                if legend.get("auto")
            ]
            legend_additions = self.generate_style_and_legend(self.main_style)
            if self.main_style:
                style_by_uid[self.main_style["uid"]] = self.main_style

            for extra_style in self.extra_styles.all():
                legend_additions += self.generate_style_and_legend(
                    extra_style.style_config
                )
                if extra_style.style_config:
                    style_by_uid[
                        extra_style.style_config["uid"]
                    ] = extra_style.style_config
                extra_style.save()

            all_legends = list(self.legends)
            for legend_addition in legend_additions:
                found = False
                for legend in all_legends:
                    if legend.get("uid") == legend_addition["uid"]:
                        # Update found legend with addition
                        legend.update(legend_addition)
                        del legend["not_updated"]
                        found = True
                        break
                if not found:
                    # Add legend to legends
                    legend_addition["title"] = f"{self.name}"
                    legend_addition["auto"] = True
                    self.legends.append(legend_addition)

            # Update legend auto status and clean unused legends
            kept_legend = []
            for legend in self.legends:
                # Do we remove that legend ?
                if legend.get("auto") and legend.get("not_updated"):
                    if not preserve_legend:
                        continue

                    # Here we try to keep deactivated legends
                    style_uid, style_prop = legend["uid"].split("__")

                    if style_uid not in style_by_uid:
                        # Style is dropped, we remove that legend
                        continue

                    prop_config = style_by_uid[style_uid]["style"].get(style_prop)

                    if not prop_config:
                        # Style prop is dropped, we remove that legend
                        continue

                    if prop_config["type"] in ["fixed", "none"]:
                        # Legend not needed anymore for this field
                        continue

                    # Here We've just need to deactivate the legend
                    del legend["auto"]
                    legend["uid"] = str(uuid.uuid4())
                    del legend["not_updated"]

                kept_legend.append(legend)

            self.legends = kept_legend

    def make_clone(self, *args, **kwargs):
        kwargs.setdefault("attrs", {"name": f"{self.name} (" + _("Copy") + ")"})
        obj = super().make_clone(*args, **kwargs)
        # fix style images references in main style
        style_text = str(json.dumps(obj.main_style))
        for i, style_image in enumerate(self.style_images.all()):
            style_text = style_text.replace(
                style_image.slug, obj.style_images.all()[i].slug
            )
        obj.main_style = json.loads(style_text)
        obj.save()
        return obj

    def __str__(self):
        return f"Layer({self.id}) - {self.name}"

    @transaction.atomic()
    def replace_source(self, new_source, fields_matches=None, dry_run=False):
        fields_matches = fields_matches or {}
        # update old field if ones from the new source
        # remove it when not present in the new source
        for filter_field in self.fields_filters.all():
            # if not fields_matches provided or found, we check with the filter_field name
            field_name = fields_matches.get(
                filter_field.field.name, filter_field.field.name
            )
            if new_source.fields.filter(name=field_name).exists():
                new_field = new_source.fields.get(name=field_name)
                if dry_run:
                    print(f"{filter_field.field.name} replaced by {new_field.name}.")
                else:
                    filter_field.field = new_field
                    filter_field.save()
            else:
                if dry_run:
                    print(f"Old field {field_name} deleted.")
                else:
                    filter_field.delete()

        # fields in the new source that don't exist in the old one are created
        for field in new_source.fields.all():
            if (
                not self.fields_filters.filter(field__name=field.name).exists()
                and field.name not in fields_matches.values()
            ):
                if dry_run:
                    print(f"New FilterField {field.name} created.")
                else:
                    self.fields_filters.create(field=field)
        if dry_run:
            print(f"{self.source} replaced by {new_source}.")
        else:
            self.source = new_source
            self.save()


class CustomStyle(models.Model):
    layer = models.ForeignKey(
        Layer, on_delete=models.CASCADE, related_name="extra_styles"
    )
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, related_name="sublayers"
    )
    style = models.JSONField(default=dict)  # To be removed
    style_config = models.JSONField(default=dict)

    interactions = models.JSONField(default=list)

    @property
    def map_style(self):
        return self.style_config.get("map_style", self.style)

    @property
    def layer_identifier(self):
        return md5(
            f"{self.source.slug}-{self.source.pk}-{self.pk}".encode("utf-8")
        ).hexdigest()


class FilterField(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    layer = models.ForeignKey(
        Layer, on_delete=models.CASCADE, related_name="fields_filters"
    )
    label = models.CharField(max_length=255, blank=True)

    order = models.IntegerField(default=0)

    filter_enable = models.BooleanField(default=False)
    filter_settings = models.JSONField(default=dict)
    format_type = models.CharField(max_length=255, default=None, null=True)

    # Whether the field can be exported
    exportable = models.BooleanField(default=False)

    # Whether the field is available in the table
    shown = models.BooleanField(default=False)

    # Whether the field is displayed by default in table
    display = models.BooleanField(default=True)

    # Config for all non handled things
    settings = models.JSONField(default=dict)

    class Meta:
        ordering = ("order",)


def style_image_path(instance, filename):
    y, m, d = timezone_today().isoformat().split("-")
    return f"terra_layer/layers/{instance.layer_id}/style_images/{y}/{m}/{d}/{filename}"


class StyleImage(models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True)
    layer = models.ForeignKey(
        Layer, related_name="style_images", on_delete=models.CASCADE
    )
    file = models.ImageField(upload_to=style_image_path)

    class Meta:
        unique_together = (("name", "layer"),)
