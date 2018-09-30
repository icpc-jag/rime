#!/usr/bin/python

import unittest

from rime.util import class_registry


class HogeBase(object):
    pass


class HogeImpl(HogeBase):
    pass


class Piyo(object):
    pass


class ClassRegistryTest(unittest.TestCase):
    def testBaseClassSuccess(self):
        r = class_registry.ClassRegistry(HogeBase)
        r.Add(HogeBase, 'Hoge')
        r.Override('Hoge', HogeImpl)
        self.assertTrue(r.classes['Hoge'] is HogeImpl)
        self.assertTrue(r.Hoge is HogeImpl)

    def testBaseClassNotSubclass(self):
        r = class_registry.ClassRegistry(HogeBase)
        r.Add(HogeBase, 'Hoge')
        self.assertRaises(AssertionError, r.Override, 'Hoge', Piyo)

    def testBaseClassNoOverride(self):
        r = class_registry.ClassRegistry(HogeBase)
        self.assertRaises(AssertionError, r.Override, 'Hoge', HogeImpl)


if __name__ == '__main__':
    unittest.main()
