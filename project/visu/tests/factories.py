import factory
from django.forms import inlineformset_factory

from project.terra_layer.tests.factories import FieldFactory
from project.visu.forms import SheetFieldInlineFormSet, SheetListFieldInlineFormSet
from project.visu.models import (
    ExtraMenuItem,
    FeatureSheet,
    SheetBlock,
    SheetBlockType,
    SheetField,
    SheetFieldThroughModel,
    SheetFieldType,
    SheetListFieldThroughModel,
    SpriteValue,
)


class SpriteValueFactory(factory.django.DjangoModelFactory):
    slug = factory.Faker("slug")

    class Meta:
        model = SpriteValue


class ExtraMenuItemFactory(factory.django.DjangoModelFactory):
    label = factory.Faker("sentence")
    href = factory.Faker("url")
    icon = factory.django.ImageField()

    class Meta:
        model = ExtraMenuItem


class SheetFieldFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SheetField

    field = factory.SubFactory(FieldFactory)
    label = factory.Sequence(lambda n: f"Field {n}")
    type = SheetFieldType.TEXTUAL


class SheetBlockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SheetBlock

    type = SheetBlockType.RADAR_PLOT
    title = factory.Sequence(lambda n: f"Block {n}")

    @factory.post_generation
    def fields(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for field in extracted:
                self.fields.add(field)


class FeatureSheetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FeatureSheet

    name = factory.Sequence(lambda n: f"Feature Sheet {n}")
    unique_identifier = factory.SubFactory(FieldFactory)

    @factory.post_generation
    def sources(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for source in extracted:
                self.sources.add(source)


SheetFieldInlineFormSetFactory = inlineformset_factory(
    SheetBlock,
    SheetFieldThroughModel,
    formset=SheetFieldInlineFormSet,
    fields=["field"],
    extra=0,
)

SheetListFieldInlineFormSetFactory = inlineformset_factory(
    FeatureSheet,
    SheetListFieldThroughModel,
    formset=SheetListFieldInlineFormSet,
    fields=["list_field"],
    extra=0,
)
