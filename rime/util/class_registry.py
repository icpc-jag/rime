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


class ClassRegistry(object):
  def __init__(self, base_class=object):
    self.classes = {}
    self.base_class = base_class

  def Get(self, name):
    return self.classes.get(name)

  def Add(self, clazz, name=None):
    if name is None:
      name = clazz.__name__
    assert name not in self.classes
    assert issubclass(clazz, self.base_class)
    self.classes[name] = clazz

  def Override(self, name, clazz):
    assert name in self.classes
    assert issubclass(clazz, self.classes[name])
    self.classes[name] = clazz

  def __getattribute__(self, name):
    try:
      return super(ClassRegistry, self).__getattribute__(name)
    except AttributeError:
      try:
        return self.classes[name]
      except KeyError:
        pass
      raise
