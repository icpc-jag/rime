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

import os
import os.path

from rime.core import commands
from rime.core import targets
from rime.core import taskgraph
from rime.basic import consts
from rime.basic.targets import problem
from rime.basic.targets import project
from rime.basic.targets import solution
from rime.basic.targets import testset
from rime.basic.util import test_summary


# Register the root command and global options.
class Default(commands.CommandBase):
  def __init__(self, parent):
    assert parent is None
    super(Default, self).__init__(None, None, '', consts.GLOBAL_HELP, parent)
    self.AddOptionEntry(commands.OptionEntry(
        'h', 'help', 'help', bool, False, None,
        'Show this help.'))
    self.AddOptionEntry(commands.OptionEntry(
        'j', 'jobs', 'parallelism', int, 0, 'n',
        'Run multiple jobs in parallel.'))
    self.AddOptionEntry(commands.OptionEntry(
        'd', 'debug', 'debug', bool, False, None,
        'Turn on debugging.'))
    self.AddOptionEntry(commands.OptionEntry(
        'C', 'cache_tests', 'cache_tests', bool, False, None,
        'Cache test results.'))
    self.AddOptionEntry(commands.OptionEntry(
        'p', 'precise', 'precise', bool, False, None,
        'Do not run timing tasks concurrently.'))
    self.AddOptionEntry(commands.OptionEntry(
        'k', 'keep_going', 'keep_going', bool, False, None,
        'Do not skip tests on failures.'))


def IsBasicTarget(obj):
  return isinstance(obj, (project.Project,
                          problem.Problem,
                          solution.Solution,
                          testset.Testset))

def RunCommon(method_name, project, args, ui):
  if args:
    base_dir = os.path.abspath(args[0])
    args = args[1:]
  else:
    base_dir = os.getcwd()

  obj = project.FindByBaseDir(base_dir)
  if not obj:
    ui.errors.Error(None,
                    'Target directory is missing or not managed by Rime.')
    return None

  if args:
    ui.errors.Error(None,
                    'Extra argument passed to %s command!' % self.name)
    return None

  if not IsBasicTarget(obj):
    ui.errors.Error(None,
                    '%s is not supported for the specified target.' % self.name)
    return None

  return getattr(obj, method_name)(ui)
  

class Build(commands.CommandBase):
  def __init__(self, parent):
    super(Build, self).__init__(
      'build',
      '[<target>]',
      'Build a target and its dependencies.',
      consts.BUILD_HELP,
      parent)

  def Run(self, project, args, ui):
    return RunCommon('Build', project, args, ui)


class Test(commands.CommandBase):
  def __init__(self, parent):
    super(Test, self).__init__(
      'test',
      '[<target>]',
      'Run tests in a target.',
      consts.TEST_HELP,
      parent)

  def Run(self, project, args, ui):
    task = RunCommon('Test', project, args, ui)
    if not task:
      return task
    @taskgraph.task_method
    def TestWrapper():
      results = yield task
      test_summary.PrintTestSummary(results, ui)
      yield results
    return TestWrapper()


class Clean(commands.CommandBase):
  def __init__(self, parent):
    super(Clean, self).__init__(
      'clean',
      '[<target>]',
      'Clean intermediate files.',
      consts.CLEAN_HELP,
      parent)

  def Run(self, project, args, ui):
    return RunCommon('Clean', project, args, ui)


commands.registry.Add(Default)
commands.registry.Add(Build)
commands.registry.Add(Test)
commands.registry.Add(Clean)
