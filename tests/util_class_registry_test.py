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

import unittest

from rime.util import class_registry


class HogeBase(object):
  pass

class HogeImpl(HogeBase):
  pass

class Piyo(object):
  pass


class ClassRegistryTest(unittest.TestCase):
  def testBaseClassSuccess(self):
    r = class_registry.ClassRegistry(HogeBase)
    r.Add(HogeBase, 'Hoge')
    r.Override('Hoge', HogeImpl)
    self.assertTrue(r.classes['Hoge'] is HogeImpl)
    self.assertTrue(r.Hoge is HogeImpl)

  def testBaseClassNotSubclass(self):
    r = class_registry.ClassRegistry(HogeBase)
    r.Add(HogeBase, 'Hoge')
    self.assertRaises(AssertionError, r.Override, 'Hoge', Piyo)

  def testBaseClassNoOverride(self):
    r = class_registry.ClassRegistry(HogeBase)
    self.assertRaises(AssertionError, r.Override, 'Hoge', HogeImpl)


if __name__ == '__main__':
  unittest.main()
