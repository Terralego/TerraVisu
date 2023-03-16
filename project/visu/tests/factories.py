from factory import Faker
from factory.django import DjangoModelFactory

from project.visu.models import SpriteValue


class SpriteValueFactory(DjangoModelFactory):
    slug = Faker("slug")
    x = 0
    y = 0
    height = 10
    width = 10
    pixel_ratio = 1
    visible = True

    class Meta:
        model = SpriteValue
