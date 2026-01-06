import factory

from project.feature_sheet.models import (
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
