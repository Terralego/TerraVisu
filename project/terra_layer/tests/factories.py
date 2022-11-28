import factory

from ..models import Layer, Scene


class SceneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Scene

    custom_icon = factory.django.ImageField()


class LayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Layer
