#!/usr/bin/python

import unittest

from six import StringIO

import mock

from rime.util import console
from rime.util import files
from rime.util import struct


class ConsoleTest(unittest.TestCase):
    def CreateStringIOConsole(self):
        return console.ConsoleBase(out=StringIO(),
                                   caps=struct.Struct(color=True,
                                                      overwrite=True))

    def testConsoleBase(self):
        c = console.ConsoleBase(out=None,
                                caps=struct.Struct(color=False,
                                                   overwrite=False))
        self.assertEqual(c.BOLD, '')
        self.assertEqual(c.UP, '')
        c = console.ConsoleBase(out=None,
                                caps=struct.Struct(color=True,
                                                   overwrite=False))
        self.assertNotEqual(c.BOLD, '')
        self.assertEqual(c.UP, '')
        c = console.ConsoleBase(out=None,
                                caps=struct.Struct(color=False,
                                                   overwrite=True))
        self.assertEqual(c.BOLD, '')
        self.assertNotEqual(c.UP, '')
        c = console.ConsoleBase(out=None,
                                caps=struct.Struct(color=True, overwrite=True))
        self.assertNotEqual(c.BOLD, '')
        self.assertNotEqual(c.UP, '')

    def testNullConsole(self):
        c = console.NullConsole()
        self.assertEqual(c.BOLD, '')
        self.assertEqual(c.UP, '')
        self.assertEqual(c.out, files.OpenNull())

    def testPrint(self):
        c = self.CreateStringIOConsole()
        c.Print('hoge')
        self.assertEqual(c.out.getvalue(), 'hoge\n')

    def testPrintWithProgress(self):
        c = self.CreateStringIOConsole()
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

    def testPrintActionWithoutObj(self):
        c = self.CreateStringIOConsole()
        c.Print = mock.MagicMock()
        c.PrintAction('HOGE', None, 'hoge', 'piyo', foo='bar')
        c.Print.assert_called_once_with(
            '\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'hoge', 'piyo',
            foo='bar')

    def testPrintActionWithObj(self):
        c = self.CreateStringIOConsole()
        c.Print = mock.MagicMock()
        c.PrintAction('HOGE', struct.Struct(fullname='name'),
                      'hoge', 'piyo', foo='bar')
        c.Print.assert_called_once_with(
            '\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'name', ':', ' ',
            'hoge', 'piyo', foo='bar')

    def testPrintActionWithObjNoArg(self):
        c = self.CreateStringIOConsole()
        c.Print = mock.MagicMock()
        c.PrintAction('HOGE', struct.Struct(fullname='name'), foo='bar')
        c.Print.assert_called_once_with(
            '\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'name', foo='bar')

    def testPrintError(self):
        c = self.CreateStringIOConsole()
        c.Print = mock.MagicMock()
        c.PrintError('hoge')
        c.Print.assert_called_once_with(
            '\x1b[31m', 'ERROR:', '\x1b[0m', ' ', 'hoge')

    def testPrintWarning(self):
        c = self.CreateStringIOConsole()
        c.Print = mock.MagicMock()
        c.PrintWarning('hoge')
        c.Print.assert_called_once_with(
            '\x1b[33m', 'WARNING:', '\x1b[0m', ' ', 'hoge')

    def testPrintLog(self):
        c = self.CreateStringIOConsole()
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


if __name__ == '__main__':
    unittest.main()
