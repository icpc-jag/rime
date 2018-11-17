import unittest

import mock

from rime.core import hooks


class TestHookPoint(unittest.TestCase):
    def test_init(self):
        hook = hooks.HookPoint()
        self.assertEqual(hook.hooks, [])

    def test_call(self):
        hook = hooks.HookPoint()
        mock_func = mock.MagicMock()
        hook.Register(mock_func)
        hook()
        mock_func.assert_called_once_with()

    def test_register(self):
        hook = hooks.HookPoint()
        mock_func = mock.MagicMock()
        res = hook.Register(mock_func)
        self.assertIs(mock_func, res)
        self.assertEqual(hook.hooks, [mock_func])
