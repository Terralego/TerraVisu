from urllib.parse import quote

from django.test import TestCase

from project.accounts.tokens import generate_token


class TokenTestCase(TestCase):
    def test_token_is_url_safe(self):
        for _ in range(100):
            token = generate_token()
            self.assertEqual(token, quote(token))
