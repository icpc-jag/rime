import sys
import unittest

import mock

from rime.core import commands, main
from rime.core import ui as ui_mod
from rime.util import console as console_mod
from rime.util.struct import Struct


class TestInternalMain(unittest.TestCase):
    def test_no_args(self):
        cmd = mock.MagicMock()
        argv = ['rime']
        args = argv[2:]
        options = Struct({'quiet': False, 'parallelism': 0, 'help': True})
        commands.Parse = mock.MagicMock()
        commands.Parse.return_value = (cmd, args, options)

        result = main.InternalMain(argv)

        self.assertEqual(result, 0)
        cmd.PrintHelp.assert_called()

    def test_help(self):
        argv = ['rime', 'help', 'clean']

        console = console_mod.TtyConsole(sys.stdout)
        console_mod.TtyConsole = mock.MagicMock()
        console_mod.TtyConsole.return_value = console

        cmd = mock.MagicMock()
        cmd.__class__ = commands.Help
        args = argv[2:]
        options = Struct({'quiet': False, 'parallelism': 0, 'help': False})
        commands.Parse = mock.MagicMock()
        commands.Parse.return_value = (cmd, args, options)

        ui = ui_mod.UiContext(options, console, cmd, None)
        ui_mod.UiContext = mock.MagicMock()
        ui_mod.UiContext.return_value = ui

        main.CheckSystem = mock.MagicMock()
        main.CheckSystem.return_value = True

        project = None
        main.LoadProject = mock.MagicMock()
        main.LoadProject.return_value = project

        result = main.InternalMain(argv)

        self.assertEqual(result, 0)
        cmd.Run.assert_called()
