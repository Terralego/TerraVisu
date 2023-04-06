import factory

from project.geosource.models import PostGISSource


class PostGISSourceFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    db_name = "test"
    db_password = "test"
    db_host = "localhost"
    geom_type = 1
    refresh = -1

    class Meta:
        model = PostGISSource
