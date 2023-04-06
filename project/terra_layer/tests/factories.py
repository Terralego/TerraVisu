import factory

from ...geosource.tests.factories import PostGISSourceFactory
from ..models import Layer, LayerGroup, Scene, StyleImage


class SceneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Scene

    custom_icon = factory.django.ImageField()


class LayerGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LayerGroup

    label = factory.Faker("name")
    view = factory.SubFactory(SceneFactory)


class LayerFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    source = factory.SubFactory(PostGISSourceFactory)

    class Meta:
        model = Layer


class StyleImageFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    file = factory.django.ImageField()

    class Meta:
        model = StyleImage
