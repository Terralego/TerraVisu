from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED


User = get_user_model()


class JWTAuthTestCase(APITestCase):
    """A short testcase to ensure JWT endpoints are set properly"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="user@test.com", password="secret")

    def test_obtain_token(self):
        response = self.client.post(
            reverse("token-obtain"), {"email": self.user.email, "password": "secret"}
        )
        self.assertEqual(HTTP_201_CREATED, response.status_code, response.json())
        self.assertIsNotNone(response.json().get("token"))

    def test_refresh_token(self):
        r = self.client.post(
            reverse("token-obtain"), {"email": self.user.email, "password": "secret"}
        )
        token = r.json().get("token")

        response = self.client.post(reverse("token-refresh"), {"token": token})
        # A new token should be send when refresh
        self.assertEqual(HTTP_201_CREATED, response.status_code, response.json())
        self.assertIsNotNone(response.json().get("token"))

    def test_verify_token(self):
        r = self.client.post(
            reverse("token-obtain"), {"email": self.user.email, "password": "secret"}
        )
        token = r.json().get("token")

        response = self.client.post(reverse("token-verify"), {"token": token})
        # Return the token, if token is valid
        self.assertEqual(HTTP_201_CREATED, response.status_code, response.json())
        self.assertIsNotNone(response.json().get("token"))
