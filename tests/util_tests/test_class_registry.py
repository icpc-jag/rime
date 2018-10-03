import unittest

from rime.util import class_registry


class HogeBase(object):
    pass


class HogeImpl(HogeBase):
    pass


class Piyo(object):
    pass


class TestClassRegistry(unittest.TestCase):
    def test_add(self):
        registry = class_registry.ClassRegistry(HogeBase)

        registry.Add(HogeBase, 'Hoge')
        self.assertIs(registry.classes['Hoge'], HogeBase)
        self.assertIs(registry.Hoge, HogeBase)
        self.assertIs(registry.Get('Hoge'), HogeBase)

    def test_add_without_name(self):
        registry = class_registry.ClassRegistry(HogeBase)

        registry.Add(HogeBase)
        self.assertIs(registry.classes['HogeBase'], HogeBase)
        self.assertIs(registry.HogeBase, HogeBase)
        self.assertIs(registry.Get('HogeBase'), HogeBase)

    def test_override(self):
        registry = class_registry.ClassRegistry(HogeBase)

        registry.Add(HogeBase, 'Hoge')
        registry.Override('Hoge', HogeImpl)
        self.assertIs(registry.classes['Hoge'], HogeImpl)
        self.assertIs(registry.Hoge, HogeImpl)
        self.assertIs(registry.Get('Hoge'), HogeImpl)

    def test_add_duplication(self):
        registry = class_registry.ClassRegistry(HogeBase)
        registry.Add(HogeBase, 'Hoge')
        with self.assertRaises(AssertionError):
            registry.Add(HogeImpl, 'Hoge')

    def test_base_class_not_subclass(self):
        registry = class_registry.ClassRegistry(HogeBase)
        registry.Add(HogeBase, 'Hoge')
        with self.assertRaises(AssertionError):
            registry.Override('Hoge', Piyo)

    def test_base_class_no_override(self):
        registry = class_registry.ClassRegistry(HogeBase)
        with self.assertRaises(AssertionError):
            registry.Override('Hoge', HogeImpl)

    def test_attribute_error(self):
        registry = class_registry.ClassRegistry(HogeBase)
        with self.assertRaises(AttributeError):
            registry.Hoge
