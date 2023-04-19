from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from project.terra_layer.filters import SceneFilterSet


class SceneFilterSetTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.filterset = SceneFilterSet
        cls.request = RequestFactory()
        cls.request.user = AnonymousUser()

    def test_filter_viewer_true(self):
        data = {'viewer': True}
        qs = self.filterset(data=data, request=self.request).qs
        self.assertEqual(qs.count(), 0)

    def test_filter_viewer_false(self):
        data = {'viewer': True}
        qs = self.filterset(data=data, request=self.request).qs
        self.assertEqual(qs.count(), 0)

    def test_filter_viewer_default(self):
        qs = self.filterset(request=self.request).qs
        self.assertEqual(qs.count(), 0)
