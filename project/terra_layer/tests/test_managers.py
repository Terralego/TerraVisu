from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase

from project.accounts.tests.factories import SuperUserFactory, UserFactory
from project.terra_layer.models import Scene
from project.terra_layer.tests.factories import (
    LayerFactory,
    LayerGroupFactory,
    SceneFactory,
)


class SceneManagerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_get_user_scenes_anonymous_with_empty_layers(self):
        """Empty scene is not available for anonymous user"""
        SceneFactory()
        scenes = Scene.objects.get_user_scenes(AnonymousUser())
        self.assertEqual(scenes.count(), 0)

    def test_get_user_scenes_anonymous_with_public_layers(self):
        """Scene with public layer is available for anonymous user"""
        group_layer = LayerGroupFactory()
        LayerFactory(group=group_layer)
        scenes = Scene.objects.get_user_scenes(AnonymousUser())
        self.assertEqual(scenes.count(), 1)

    def test_get_user_scenes_anonymous_with_private_layers(self):
        """Scene with private layer is not available for anonymous user"""
        group_layer = LayerGroupFactory()
        layer = LayerFactory(group=group_layer)
        layer.source.groups.add(Group.objects.create(name="test"))
        scenes = Scene.objects.get_user_scenes(AnonymousUser())
        self.assertEqual(scenes.count(), 0)

    def test_get_user_scenes_authenticated_with_public_layers(self):
        group_layer = LayerGroupFactory()
        LayerFactory(group=group_layer)
        user = UserFactory()
        scenes = Scene.objects.get_user_scenes(user)
        self.assertEqual(scenes.count(), 1)

    def test_get_user_scenes_authenticated_with_private_layers_group_match(self):
        """Scene with private layer is available for authenticated user if group match"""
        user = UserFactory()
        group_layer = LayerGroupFactory()
        layer = LayerFactory(group=group_layer)
        user_group = Group.objects.create(name="test")
        user_group.user_set.add(user)
        layer.source.groups.add(user_group)

        scenes = Scene.objects.get_user_scenes(user)
        self.assertEqual(scenes.count(), 1)

    def test_get_user_scenes_superuser(self):
        """Superuser can access all scenes"""
        user = SuperUserFactory()
        group_layer = LayerGroupFactory()
        layer = LayerFactory(group=group_layer)
        layer.source.groups.add(Group.objects.create(name="test2"))
        scenes = Scene.objects.get_user_scenes(user)
        self.assertEqual(scenes.count(), 1)
