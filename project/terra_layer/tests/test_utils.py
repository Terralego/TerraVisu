from django.test import TestCase

from ..utils import dict_merge


class UtilsTestCase(TestCase):
    def test_dict_merge_add_key(self):
        merged = dict_merge(
            {"initialState": {"active": "True", "opacity": 1}}, {"test": "test"}
        )
        self.assertEqual(
            merged, {"initialState": {"active": "True", "opacity": 1}, "test": "test"}
        )

    def test_dict_merge_do_not_add_key(self):
        merged = dict_merge(
            {"initialState": {"active": "True", "opacity": 1}, "other": {"other": 1}},
            {"initialState": "test", "test": "test", "other": {"other": 2}},
            False,
        )
        self.assertEqual(merged, {"initialState": "test", "other": {"other": 2}})
