import unittest

from rime.util import class_registry
from rime.util import module_loader

from . import test_package


class TestModuleLoader(unittest.TestCase):
    def test_load_module(self):
        res = module_loader.LoadModule(
            'tests.util_tests.test_package.test_module1')
        self.assertTrue(res)
        self.assertIs(registry.test_module1, test_package.test_module1.Test1)

    def test_load_package(self):
        module_loader.LoadPackage('tests.util_tests.test_package')
        self.assertIs(registry.test_module1, test_package.test_module1.Test1)
        self.assertIs(registry.test_module2,
                      test_package.test_subpackage.test_module2.Test2)


registry = class_registry.ClassRegistry()
