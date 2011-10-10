#!/usr/bin/python
#
# Copyright (c) 2011 Rime Project.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import StringIO
import unittest

import mox

from rime.util import console
from rime.util import files
from rime.util import struct


class ConsoleTest(unittest.TestCase):
  def setUp(self):
    self.mox = mox.Mox()

  def tearDown(self):
    self.mox.UnsetStubs()

  def CreateStringIOConsole(self):
    return console.ConsoleBase(out=StringIO.StringIO(),
                               caps=struct.Struct(color=True, overwrite=True))

  def testConsoleBase(self):
    c = console.ConsoleBase(out=None,
                            caps=struct.Struct(color=False, overwrite=False))
    self.assertEqual(c.BOLD, '')
    self.assertEqual(c.UP, '')
    c = console.ConsoleBase(out=None,
                            caps=struct.Struct(color=True, overwrite=False))
    self.assertNotEqual(c.BOLD, '')
    self.assertEqual(c.UP, '')
    c = console.ConsoleBase(out=None,
                            caps=struct.Struct(color=False, overwrite=True))
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
    self.mox.StubOutWithMock(c, 'Print')
    c.Print('\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ',
            'hoge', 'piyo', foo='bar')
    self.mox.ReplayAll()
    c.PrintAction('HOGE', None, 'hoge', 'piyo', foo='bar')
    self.mox.VerifyAll()

  def testPrintActionWithObj(self):
    c = self.CreateStringIOConsole()
    self.mox.StubOutWithMock(c, 'Print')
    c.Print('\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'name', ':', ' ',
            'hoge', 'piyo', foo='bar')
    self.mox.ReplayAll()
    c.PrintAction('HOGE', struct.Struct(fullname='name'),
                  'hoge', 'piyo', foo='bar')
    self.mox.VerifyAll()

  def testPrintActionWithObjNoArg(self):
    c = self.CreateStringIOConsole()
    self.mox.StubOutWithMock(c, 'Print')
    c.Print('\x1b[32m', '[   HOGE   ]', '\x1b[0m', ' ', 'name', foo='bar')
    self.mox.ReplayAll()
    c.PrintAction('HOGE', struct.Struct(fullname='name'), foo='bar')
    self.mox.VerifyAll()

  def testPrintError(self):
    c = self.CreateStringIOConsole()
    self.mox.StubOutWithMock(c, 'Print')
    c.Print('\x1b[31m', 'ERROR:', '\x1b[0m', ' ', 'hoge')
    self.mox.ReplayAll()
    c.PrintError('hoge')
    self.mox.VerifyAll()

  def testPrintWarning(self):
    c = self.CreateStringIOConsole()
    self.mox.StubOutWithMock(c, 'Print')
    c.Print('\x1b[33m', 'WARNING:', '\x1b[0m', ' ', 'hoge')
    self.mox.ReplayAll()
    c.PrintWarning('hoge')
    self.mox.VerifyAll()

  def testPrintLog(self):
    c = self.CreateStringIOConsole()
    self.mox.StubOutWithMock(c, 'Print')
    c.Print('')
    c.Print('hoge')
    c.Print('')
    c.Print('piyo')
    c.Print('')
    self.mox.ReplayAll()
    c.PrintLog('\nhoge\n\npiyo\n\n')
    self.mox.VerifyAll()


if __name__ == '__main__':
  unittest.main()
