from django.contrib.auth import get_user_model
from django.test import TestCase

from project.accounts.oidc import get_user

User = get_user_model()


class OIDCCallbackTestCase(TestCase):
    def test_oidc_callback_create_user(self):
        """New user should be created after callback"""
        id_token = {
            "email": "toto@terravisu.com",
            "sub": "123456789",
        }
        user = get_user(id_token)
        self.assertEqual(user.email, id_token.get("email"))
        self.assertEqual(user.properties["openid_sub"], id_token.get("sub"))

    def test_oidc_callback_update_user(self):
        """User should be updated after callback"""
        id_token = {
            "email": "toto@terravisu.com",
            "sub": "123456789",
        }
        user = User.objects.create(email=id_token["email"])
        self.assertEqual(User.objects.all().count(), 1)
        callback_user = get_user(id_token)
        self.assertEqual(callback_user.properties["openid_sub"], id_token.get("sub"))
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(user.pk, callback_user.pk)
