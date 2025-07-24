import factory
from django.contrib.gis.geos import Point
from geostore.models import Feature

from project.accounts.tests.factories import UserFactory

from ...geosource.tests.factories import PostGISSourceFactory
from ..models import (
    Layer,
    LayerGroup,
    Report,
    ReportConfig,
    Scene,
    StyleImage,
)


class SceneFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    custom_icon = factory.django.ImageField()

    class Meta:
        model = Scene


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

    @factory.post_generation
    def _set_layer_identifier(obj, create, extracted, **kwargs):
        # Set a mock layer_identifier directly on the instance
        obj.layer_identifier = f"test-layer-{obj.pk}"


class FeatureFactory(factory.django.DjangoModelFactory):
    geom = factory.LazyFunction(lambda: Point(0, 0))
    identifier = factory.LazyFunction(lambda: str(factory.Faker("uuid4")))
    properties = factory.Dict(
        {"name": factory.Faker("word"), "description": factory.Faker("sentence")}
    )
    layer = factory.SubFactory("geostore.tests.factories.LayerFactory")

    class Meta:
        model = Feature


class StyleImageFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    file = factory.django.ImageField()

    class Meta:
        model = StyleImage


class ReportConfigFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"Config {n}")
    layer = factory.SubFactory(LayerFactory)

    class Meta:
        model = ReportConfig


class ReportFactory(factory.django.DjangoModelFactory):
    config = factory.SubFactory(ReportConfigFactory)
    feature = factory.SubFactory(FeatureFactory)
    content = factory.Dict(
        {
            "field1": factory.Faker("text", max_nb_chars=100),
            "field2": factory.Faker("text", max_nb_chars=100),
        }
    )
    user = factory.SubFactory(UserFactory)
    layer = factory.SelfAttribute("config.layer")

    class Meta:
        model = Report
