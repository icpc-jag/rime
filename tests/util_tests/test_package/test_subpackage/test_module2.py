from tests.util_tests import test_module_loader


class Test2(object):
    pass


test_module_loader.registry.Add(Test2, 'test_module2')
