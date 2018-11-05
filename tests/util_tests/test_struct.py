import unittest

from rime.util import struct


class TestStruct(unittest.TestCase):
    def test_dict_attr(self):
        self.assertEqual(struct.Struct.items, dict.items)

    def test_constructor(self):
        s = struct.Struct(test_attr='test_obj')
        self.assertEqual(s.test_attr, 'test_obj')
        self.assertEqual(s['test_attr'], 'test_obj')

    def test_add_attr(self):
        s = struct.Struct()
        s.test_attr = 'test_obj'
        self.assertEqual(s.test_attr, 'test_obj')

    def test_add_key(self):
        s = struct.Struct()
        s['test_attr'] = 'test_obj'
        self.assertEqual(s.test_attr, 'test_obj')
        self.assertEqual(s['test_attr'], 'test_obj')

    def test_attribute_error(self):
        s = struct.Struct()
        with self.assertRaises(AttributeError):
            s.test_attr
