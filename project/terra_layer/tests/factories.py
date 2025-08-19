import factory
from django.contrib.gis.geos import Point
from geostore.models import Feature

from project.accounts.tests.factories import UserFactory

from ...geosource.models import Field
from ...geosource.tests.factories import PostGISSourceFactory
from ..models import (
    Declaration,
    DeclarationConfig,
    DeclarationField,
    DeclarationFile,
    Layer,
    LayerGroup,
    ManagerMessage,
    Report,
    ReportConfig,
    ReportFile,
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


class FieldFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Field

    source = factory.SubFactory(PostGISSourceFactory)
    name = factory.Faker("word")


class LayerFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    source = factory.SubFactory(PostGISSourceFactory)
    main_field = factory.SubFactory(FieldFactory)

    class Meta:
        model = Layer

    @factory.post_generation
    def _set_layer_identifier(obj, create, extracted, **kwargs):
        # Set a mock layer_identifier directly on the instance
        obj.layer_identifier = f"test-layer-{obj.pk}"

    @factory.post_generation
    def _set_source(obj, create, extracted, **kwargs):
        # Ensure layer and main_field have same source
        obj.source = obj.main_field.source


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
    content = [
        {
            "sourceFieldId": 345,
            "value": "my_field_1",
            "label": "The Field One",
            "content": "Some example content for testing purposes",
        },
        {
            "sourceFieldId": 123,
            "value": "my_field_2",
            "label": "The Field Two",
            "content": "Some example content for testing purposes with additional information that provides context",
        },
        {
            "free_comment": "Another example with some extra information that was provided after the fields"
        },
    ]
    user = factory.SubFactory(UserFactory)
    layer = factory.SelfAttribute("config.layer")

    class Meta:
        model = Report


class ReportFileFactory(factory.django.DjangoModelFactory):
    report = factory.SubFactory(ReportFactory)
    file = factory.django.FileField()

    class Meta:
        model = ReportFile


class DeclarationConfigFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Config {n}")

    class Meta:
        model = DeclarationConfig


class DeclarationFieldFactory(factory.django.DjangoModelFactory):
    config = factory.SubFactory(DeclarationConfigFactory)
    title = factory.Sequence(lambda n: f"Declaration field {n}")
    helptext = factory.Sequence(lambda n: f"Some help text for declaration field {n}")

    class Meta:
        model = DeclarationField


class ManagerMessageFactory(factory.django.DjangoModelFactory):
    text = "Test text"

    class Meta:
        model = ManagerMessage


class DeclarationFactory(factory.django.DjangoModelFactory):
    geom = factory.LazyFunction(lambda: Point(10000, 200000))
    content = [
        {
            "title": "The title of the field",
            "value": "Some message sent by a user though the feedback system",
        },
        {
            "title": "The Field Two",
            "value": "Some example content for testing purposes with additional information that provides context",
        },
        {
            "free_comment": "Another example with some extra information that was provided after the fields"
        },
    ]

    class Meta:
        model = Declaration


class AuthentifiedDeclarationFactory(DeclarationFactory):
    user = factory.SubFactory(UserFactory)


class UnauthentifiedDeclarationFactory(DeclarationFactory):
    email = "test@email.fr"


class DeclarationFileFactory(factory.django.DjangoModelFactory):
    declaration = factory.SubFactory(UnauthentifiedDeclarationFactory)
    file = factory.django.FileField()

    class Meta:
        model = DeclarationFile
