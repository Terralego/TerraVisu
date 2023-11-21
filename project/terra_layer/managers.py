from django.db import models
from django.db.models import CharField, Func, Value
from django.db.models.functions import Cast, Concat


class SceneManager(models.Manager):
    def get_user_scenes(self, user):
        """Return all scenes that the user can access"""
        pks = []
        for scene in self.get_queryset():
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
        return self.get_queryset().filter(pk__in=pks)


class LayerManager(models.Manager):
    def get_queryset(self):
        """Annotate source and add layer_identifier with DATABASE function"""
        qs = super().get_queryset()
        qs = (
            qs.select_related(
                "source",
            )
            .alias(
                hash_key=Concat(
                    "source__slug", Value("-"), Cast("id", output_field=CharField())
                )
            )
            .annotate(layer_identifier=Func("hash_key", function="MD5"))
        )
        return qs
