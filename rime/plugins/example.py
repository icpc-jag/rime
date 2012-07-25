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

from rime.core import commands

class Example(commands.CommandBase):
  def __init__(self, parent):
    super(Example, self).__init__(
      'example',
      '',
      'Example command.',
      'Example help.',
      parent)

  def Run(self, project, args, ui):
    ui.console.Print('Hello, world!')
    ui.console.Print()
    ui.console.Print('Project:')
    ui.console.Print('  %s' % repr(project))
    ui.console.Print()
    ui.console.Print('Parameters:')
    for i, arg in enumerate(args):
      ui.console.Print('  args[%s] = "%s"' % (i, arg))
    ui.console.Print()
    ui.console.Print('Options:')
    for key, value in ui.options.items():
      ui.console.Print('  options.%s = %s' % (key, value))

commands.registry.Add(Example)
