import os
import sys
import unittest

import mock

from rime.core import targets


class Target(targets.TargetBase):
    CONFIG_FILENAME = 'TEST_TARGET'

    @staticmethod
    def func():
        pass

    @staticmethod
    def reload(called=[]):
        if not called:
            called.append(0)
            raise targets.ReloadConfiguration()


def _get_target(name):
    return os.path.join(os.path.dirname(__file__), 'test_targets', name)


class TestTargetBase(unittest.TestCase):
    def test_init(self):
        target = Target(None, 'test_dir', None)
        self.assertEqual(target.name, '<root>')
        self.assertEqual(target.base_dir, 'test_dir')
        self.assertIsNone(target.parent)
        self.assertIsNone(target.fullname)
        self.assertEqual(target.config_file, 'test_dir/TEST_TARGET')
        self.assertEqual(target.exports, {})
        self.assertEqual(target.configs, {})
        self.assertFalse(target._loaded)

    def test_init_with_name(self):
        target = Target('target', 'test_dir', None)
        self.assertEqual(target.name, 'target')
        self.assertEqual(target.base_dir, 'test_dir')
        self.assertIsNone(target.parent)
        self.assertEqual(target.fullname, 'target')
        self.assertEqual(target.config_file, 'test_dir/TEST_TARGET')
        self.assertEqual(target.exports, {})
        self.assertEqual(target.configs, {})
        self.assertFalse(target._loaded)

    def test_init_with_parent(self):
        parent = Target(None, 'parent_dir', None)
        target = Target('target', 'test_dir', parent)
        self.assertEqual(target.name, 'target')
        self.assertEqual(target.base_dir, 'test_dir')
        self.assertIs(target.parent, parent)
        self.assertEqual(target.fullname, 'target')
        self.assertEqual(target.config_file, 'test_dir/TEST_TARGET')
        self.assertEqual(target.exports, {})
        self.assertEqual(target.configs, {})
        self.assertFalse(target._loaded)

    def test_init_with_2_parents(self):
        parent1 = Target(None, 'parent1dir', None)
        parent2 = Target('parent2', 'parent2dir', parent1)
        target = Target('target', 'test_dir', parent2)
        self.assertEqual(target.name, 'target')
        self.assertEqual(target.base_dir, 'test_dir')
        self.assertIs(target.parent, parent2)
        self.assertEqual(target.fullname, 'parent2/target')
        self.assertEqual(target.config_file, 'test_dir/TEST_TARGET')
        self.assertEqual(target.exports, {})
        self.assertEqual(target.configs, {})
        self.assertFalse(target._loaded)

    def test_export(self):
        target = Target(None, 'test_dir', None)
        target.Export(Target.func)
        self.assertEqual(target.exports, {Target.func.__name__: Target.func})

    def test_export_with_name(self):
        target = Target(None, 'test_dir', None)
        target.Export(Target.func, 'test_func')
        self.assertEqual(target.exports, {'test_func': Target.func})

    def test_export_duplication(self):
        target = Target(None, 'test_dir', None)
        target.Export(Target.func)
        with self.assertRaises(AssertionError):
            target.Export(Target.func)

    def test_load(self):
        Target.mock_func = mock.MagicMock()
        target = Target(None, _get_target('test_target'), None)
        target.Export(Target.mock_func, 'func')
        target.Load(None)
        Target.mock_func.assert_called_once_with()
        self.assertTrue(target._loaded)

    def test_load_twice(self):
        target = Target(None, _get_target('test_target'), None)
        target.Export(Target.func)
        target.Load(None)
        with self.assertRaises(AssertionError):
            target.Load(None)

    def test_load_reload(self):
        target = Target(None, _get_target('test_target_reload'), None)
        target.Export(Target.reload)
        with self.assertRaises(targets.ReloadConfiguration):
            target.Load(None)

        target = Target(None, _get_target('test_target_reload'), None)
        target.Export(Target.reload)
        target.Load(None)

    def test_load_error(self):
        target = Target(None, _get_target('test_target_error'), None)
        with self.assertRaises(targets.ConfigurationError, msg='test error'):
            target.Load(None)

    def test_load_no_config(self):
        target = Target(None, _get_target('test_target_no_config'), None)
        err_message = 'cannot read file: %s' % target.config_file
        with self.assertRaises(targets.ConfigurationError, msg=err_message):
            target.Load(None)

    def test_find_by_base_dir(self):
        target = Target(None, 'test_dir', None)
        self.assertIs(target.FindByBaseDir('test_dir'), target)
        self.assertIsNone(target.FindByBaseDir('dummy'))

    def test_can_load_from(self):
        path = _get_target('test_target')
        target = Target(None, path, None)
        self.assertTrue(target.CanLoadFrom(path))

    def test_can_load_from_no_config(self):
        path = _get_target('test_target_no_config')
        target = Target(None, path, None)
        self.assertFalse(target.CanLoadFrom(path))


class TestProject(unittest.TestCase):
    def test_project(self):
        path = _get_target('test_project')
        project = targets.Project(None, path, None)
        err_message = 'use_plugin(\'example\')'
        with self.assertRaises(targets.ReloadConfiguration, msg=err_message):
            project.Load(None)
        self.assertIn('rime.plugins.example', sys.modules)

        project = targets.Project(None, path, None)
        project.Load(None)

    def test_project_error(self):
        path = _get_target('test_project_error')
        project = targets.Project(None, path, None)
        err_message = 'Failed to load a plugin: dummy'
        with self.assertRaises(targets.ConfigurationError, msg=err_message):
            project.Load(None)
