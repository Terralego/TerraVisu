import factory

from project.geosource.models import PostGISSource, WMTSSource


class PostGISSourceFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    db_name = "test"
    db_password = "test"
    db_host = "localhost"
    geom_type = 1
    refresh = -1

    class Meta:
        model = PostGISSource


class WMTSSourceFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    url = factory.Faker("url")
    tile_size = 256

    class Meta:
        model = WMTSSource
