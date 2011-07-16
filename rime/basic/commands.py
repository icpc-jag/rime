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
from rime.core import targets
from rime.basic.targets import problem
from rime.basic.targets import project
from rime.basic.targets import solution
from rime.basic.targets import testset


def Build(obj, args, ui):
  """Entry point for build command."""
  if args:
    ui.console.PrintError('Extra argument passed to build command!')
    return None

  if isinstance(obj, (targets.Project,
                      targets.Problem,
                      targets.Solution,
                      targets.Testset)):
    return obj.Build(ui)

  ui.console.PrintError('Build is not supported for the specified target.')
  return None


def Test(obj, args, ui):
  """Entry point for test command."""
  if args:
    ui.console.PrintError('Extra argument passed to test command!')
    return None

  if isinstance(obj, (targets.Project,
                      targets.Problem,
                      targets.Solution,
                      targets.Testset)):
    return obj.Test(ui)

  ui.console.PrintError('Test is not supported for the specified target.')
  return None


def Clean(obj, args, ui):
  """Entry point for clean command."""
  if args:
    ui.console.PrintError('Extra argument passed to clean command!')
    return None

  if isinstance(obj, (targets.Project,
                      targets.Problem,
                      targets.Solution,
                      targets.Testset)):
    return obj.Clean(ui)

  ui.console.PrintError('Clean is not supported for the specified target.')
  return None


commands.RegisterCommand('build', Build, """\
Build a target.
""")

commands.RegisterCommand('test', Test, """\
Run tests.
""")

commands.RegisterCommand('clean', Clean, """\
Clean intermediate files.
""")
