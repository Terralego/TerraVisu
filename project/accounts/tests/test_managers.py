from django.test import TestCase

from project.accounts.models import User


class UserManagerTesCase(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email="user1@email.com", password="password")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(self.client.login(email=user.email, password="password"))

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="user2@email.com", password="password"
        )
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(self.client.login(email=user.email, password="password"))
