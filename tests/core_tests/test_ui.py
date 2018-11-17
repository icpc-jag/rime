import sys
import unittest

import mock

from rime.core import targets
from rime.core import taskgraph
from rime.core import ui
from rime.util import console
from rime.util import struct


class TestUiContext(unittest.TestCase):
    def test_init(self):
        commands = {}
        options = struct.Struct()
        null_console = console.NullConsole()
        graph = taskgraph.SerialTaskGraph()
        ui_obj = ui.UiContext(options, null_console, commands, graph)
        self.assertIs(ui_obj.options, options)
        self.assertIs(ui_obj.console, null_console)
        self.assertIs(ui_obj.commands, commands)
        self.assertIs(ui_obj.graph, graph)
        self.assertIsInstance(ui_obj.errors, ui.ErrorRecorder)
        self.assertIs(ui_obj.errors.ui, ui_obj)


class Target(targets.TargetBase):
    CONFIG_FILENAME = 'TEST_TARGET'


class TestErrorRecorder(unittest.TestCase):
    @staticmethod
    def get_error_recoder(debug=False):
        commands = {}
        options = struct.Struct()
        options.debug = debug
        null_console = console.NullConsole()
        null_console.PrintError = mock.MagicMock()
        null_console.PrintWarning = mock.MagicMock()
        null_console.PrintLog = mock.MagicMock()
        null_console.Print = mock.MagicMock()
        graph = taskgraph.SerialTaskGraph()
        ui_obj = ui.UiContext(options, null_console, commands, graph)
        return ui.ErrorRecorder(ui_obj)

    def test_init(self):
        commands = {}
        options = struct.Struct()
        null_console = console.NullConsole()
        graph = taskgraph.SerialTaskGraph()
        ui_obj = ui.UiContext(options, null_console, commands, graph)
        error_recorder = ui.ErrorRecorder(ui_obj)
        self.assertIs(error_recorder.ui, ui_obj)
        self.assertEqual(error_recorder.errors, [])
        self.assertEqual(error_recorder.warnings, [])
        self.assertFalse(error_recorder.HasError())
        self.assertFalse(error_recorder.HasWarning())

    def test_error(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        error_recorder.Error(target, 'test reason')

        msg = 'test_target: test reason'
        error_recorder.ui.console.PrintError.assert_called_once_with(msg)
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(error_recorder.errors, [msg])
        self.assertTrue(error_recorder.HasError())

    def test_error_excinfo(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Error(target, 'test reason', sys.exc_info())

        error_recorder.ui.console.PrintError.assert_called()
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(len(error_recorder.errors), 1)
        self.assertTrue(error_recorder.HasError())

    def test_error_excinfo_debug(self):
        error_recorder = self.get_error_recoder(debug=True)
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Error(target, 'test reason', sys.exc_info())

        error_recorder.ui.console.PrintError.assert_called()
        error_recorder.ui.console.PrintLog.assert_called()
        self.assertEqual(len(error_recorder.errors), 1)
        self.assertTrue(error_recorder.HasError())

    def test_error_quiet(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        error_recorder.Error(target, 'test reason', quiet=True)

        msg = 'test_target: test reason'
        error_recorder.ui.console.PrintError.assert_not_called()
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(error_recorder.errors, [msg])
        self.assertTrue(error_recorder.HasError())

    def test_warning(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        error_recorder.Warning(target, 'test reason')

        msg = 'test_target: test reason'
        error_recorder.ui.console.PrintWarning.assert_called_once_with(msg)
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(error_recorder.warnings, [msg])
        self.assertTrue(error_recorder.HasWarning())

    def test_warning_excinfo(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Warning(target, 'test reason', sys.exc_info())

        error_recorder.ui.console.PrintWarning.assert_called()
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(len(error_recorder.warnings), 1)
        self.assertTrue(error_recorder.HasWarning())

    def test_warning_excinfo_debug(self):
        error_recorder = self.get_error_recoder(debug=True)
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Warning(target, 'test reason', sys.exc_info())

        error_recorder.ui.console.PrintWarning.assert_called()
        error_recorder.ui.console.PrintLog.assert_called()
        self.assertEqual(len(error_recorder.warnings), 1)
        self.assertTrue(error_recorder.HasWarning())

    def test_warning_quiet(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        error_recorder.Warning(target, 'test reason', quiet=True)

        msg = 'test_target: test reason'
        error_recorder.ui.console.PrintWarning.assert_not_called()
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(error_recorder.warnings, [msg])
        self.assertTrue(error_recorder.HasWarning())

    def test_exception(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Exception(target)

        error_recorder.ui.console.PrintError.assert_called()
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(len(error_recorder.errors), 1)
        self.assertTrue(error_recorder.HasError())

    def test_exception_exc_info(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Exception(target, sys.exc_info())

        error_recorder.ui.console.PrintError.assert_called()
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(len(error_recorder.errors), 1)
        self.assertTrue(error_recorder.HasError())

    def test_exception_quit(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Exception(target, quiet=True)

        error_recorder.ui.console.PrintError.assert_not_called()
        error_recorder.ui.console.PrintLog.assert_not_called()
        self.assertEqual(len(error_recorder.errors), 1)
        self.assertTrue(error_recorder.HasError())

    def test_exception_debug(self):
        error_recorder = self.get_error_recoder(debug=True)
        target = Target('test_target', 'test_dir', None)
        try:
            raise RuntimeError()
        except RuntimeError:
            error_recorder.Exception(target)

        error_recorder.ui.console.PrintError.assert_called()
        error_recorder.ui.console.PrintLog.assert_called()
        self.assertEqual(len(error_recorder.errors), 1)
        self.assertTrue(error_recorder.HasError())

    def test_print_summary(self):
        error_recorder = self.get_error_recoder()
        target = Target('test_target', 'test_dir', None)
        error_recorder.Error(target, 'test error', quiet=True)
        error_recorder.Warning(target, 'test warning', quiet=True)
        error_recorder.PrintSummary()

        error_msg = 'test_target: test error'
        warning_msg = 'test_target: test warning'
        summary_msg = 'Total 1 errors, 1 warnings'
        ui_console = error_recorder.ui.console
        ui_console.PrintError.assert_called_once_with(error_msg)
        ui_console.PrintWarning.assert_called_once_with(warning_msg)
        ui_console.Print.assert_called_once_with(summary_msg)
