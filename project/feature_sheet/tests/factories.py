import factory

from project.feature_sheet.models import (
    FeatureSheet,
    SheetBlock,
    SheetBlockType,
    SheetField,
    SheetFieldType,
)
from project.terra_layer.tests.factories import FieldFactory


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
    def accessible_from(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for layer in extracted:
                self.accessible_from.add(layer)
