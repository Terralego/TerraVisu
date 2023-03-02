import factory
from factory import faker

from project.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = faker.Faker("email")
    password = factory.PostGenerationMethodCall("set_password", "password")
    is_active = True


class SuperUserFactory(UserFactory):
    is_superuser = True
    is_staff = True
