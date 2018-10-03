from tests.util_tests import test_module_loader


class Test1(object):
    pass


test_module_loader.registry.Add(Test1, 'test_module1')
