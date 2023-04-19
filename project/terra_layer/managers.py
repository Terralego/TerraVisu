from django.db import models


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
