import sys
import unittest

import mock

from rime.util import console
from rime.util import files
from rime.util import struct

if sys.version_info[0] == 2:
    from StringIO import StringIO
else:
    from io import StringIO


class TestConsole(unittest.TestCase):
    def create_stringio_console(self):
        return console.ConsoleBase(
            out=StringIO(), caps=struct.Struct(color=True, overwrite=True))

    def test_console_base(self):
        c = console.ConsoleBase(
            out=None, caps=struct.Struct(color=False, overwrite=False))
        self.assertEqual(c.BOLD, '')
        self.assertEqual(c.UP, '')
        c = console.ConsoleBase(
            out=None, caps=struct.Struct(color=True, overwrite=False))
        self.assertEqual(c.BOLD, '\x1b[1m')
        self.assertEqual(c.UP, '')
        c = console.ConsoleBase(
            out=None, caps=struct.Struct(color=False, overwrite=True))
        self.assertEqual(c.BOLD, '')
        self.assertEqual(c.UP, '\x1b[1A')
        c = console.ConsoleBase(
            out=None, caps=struct.Struct(color=True, overwrite=True))
        self.assertEqual(c.BOLD, '\x1b[1m')
        self.assertEqual(c.UP, '\x1b[1A')

    def test_print(self):
        c = self.create_stringio_console()
        c.Print('hoge')
        self.assertEqual(c.out.getvalue(), 'hoge\n')

    def test_print_with_progress(self):
        c = self.create_stringio_console()
        c.Print('a')
        c.Print('b', progress=True)
        c.Print('c')
        c.Print('d', progress=True)
        c.Print('e', progress=True)
        c.Print('f')
        c.Print('g')
        self.assertEqual(c.out.getvalue(),
                         'a\n'
                         'b\n'
                         '\x1b[1A\rc\x1b[K\n'
                         'd\n'
                         '\x1b[1A\re\x1b[K\n'
                         '\x1b[1A\rf\x1b[K\n'
                         'g\n')

    def test_quiet(self):
        c = self.create_stringio_console()
        c.set_quiet()
        c.Print('hoge', progress=True)
        self.assertEqual(c.out.getvalue(), '')

    def test_print_action_without_obj(self):
        c = self.create_stringio_console()
        c.Print = mock.MagicMock()
        c.PrintAction('HOGE', None, 'hoge', 'piyo', foo='bar')
        c.Print.assert_called_once_with(
            '\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'hoge', 'piyo',
            foo='bar')

    def test_print_action_with_obj(self):
        c = self.create_stringio_console()
        c.Print = mock.MagicMock()
        c.PrintAction('HOGE', struct.Struct(fullname='name'),
                      'hoge', 'piyo', foo='bar')
        c.Print.assert_called_once_with(
            '\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'name', ':', ' ',
            'hoge', 'piyo', foo='bar')

    def test_print_action_with_obj_no_arg(self):
        c = self.create_stringio_console()
        c.Print = mock.MagicMock()
        c.PrintAction('HOGE', struct.Struct(fullname='name'), foo='bar')
        c.Print.assert_called_once_with(
            '\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'name', foo='bar')

    def test_print_error(self):
        c = self.create_stringio_console()
        c.Print = mock.MagicMock()
        c.PrintError('hoge')
        c.Print.assert_called_once_with(
            '\x1b[31m', 'ERROR:', '\x1b[0m', ' ', 'hoge')

    def test_print_warning(self):
        c = self.create_stringio_console()
        c.Print = mock.MagicMock()
        c.PrintWarning('hoge')
        c.Print.assert_called_once_with(
            '\x1b[33m', 'WARNING:', '\x1b[0m', ' ', 'hoge')

    def test_print_log(self):
        c = self.create_stringio_console()
        c.Print = mock.MagicMock()
        c.PrintLog('\nhoge\n\npiyo\n\n')
        expected = [
            mock.call(''),
            mock.call('hoge'),
            mock.call(''),
            mock.call('piyo'),
            mock.call('')
        ]
        self.assertEqual(c.Print.mock_calls, expected)

    def test_print_none_log(self):
        c = self.create_stringio_console()
        c.Print = mock.MagicMock()
        c.PrintLog(None)
        self.assertEqual(c.Print.mock_calls, [])

    def test_tty_console(self):
        c = console.TtyConsole(sys.stdout)
        self.assertEqual(c.BOLD, '')
        self.assertEqual(c.UP, '')
        self.assertEqual(c.out, sys.stdout)

    def test_null_console(self):
        c = console.NullConsole()
        self.assertEqual(c.BOLD, '')
        self.assertEqual(c.UP, '')
        self.assertEqual(c.out, files.OpenNull())
