from django.test import TestCase
from faker import Faker

from project.accounts.serializers import UserSerializer


class UserSerializerTestCase(TestCase):
    def test_created_user_can_login(self):
        """Created user by serializer API can login with its provided credentials"""
        fake = Faker()
        email = fake.email()
        password = fake.password()
        data = {"email": email, "password": password}
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), data)
        serializer.save()
        self.assertTrue(self.client.login(email=email, password=password))
