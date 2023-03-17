import factory

from project.visu.models import ExtraMenuItem, SpriteValue


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
