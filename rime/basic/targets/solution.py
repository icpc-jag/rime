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

import os.path

from rime.basic.targets import problem
from rime.core import codes
from rime.core import targets
from rime.core import taskgraph
from rime.util import files


class Solution(targets.TargetBase, problem.ProblemComponentMixin):
  """Solution target."""

  CONFIG_FILENAME = 'SOLUTION'

  def __init__(self, name, base_dir, parent):
    assert isinstance(parent, problem.Problem)
    super(Solution, self).__init__(name, base_dir, parent)
    self.project = parent.project
    self.problem = parent
    problem.ProblemComponentMixin.__init__(self)

  def PreLoad(self, ui):
    super(Solution, self).PreLoad(ui)
    self._codes = []
    self.correct = True
    self.challenge_cases = None
    self.exports.update(
      codes.ExportDictionary('%s_solution', self._codes,
                             src_dir=self.src_dir,
                             out_dir=self.out_dir))

  def PostLoad(self, ui):
    super(Solution, self).PostLoad(ui)
    if len(self._codes) == 0:
      self._CompatGuessSolution(ui)
    if len(self._codes) >= 2:
      raise targets.ConfigurationError('multiple solutions')
    if len(self._codes) == 0:
      raise targets.ConfigurationError('no solution definition found')
    self.code = self._codes[0]
    self._ReadCompatSettings(ui)

  def _CompatGuessSolution(self, ui):
    for filename in files.ListDir(self.src_dir):
      code = codes.CreateCodeByExtension(filename, self.src_dir, self.out_dir)
      if code is not None:
        self._codes.append(code)

  def _ReadCompatSettings(self, ui):
    # Decide if this solution is correct or not.
    challenge_cases = self.configs.get('CHALLENGE_CASES')
    if challenge_cases is not None:
      self.correct = False
      self.challenge_cases = self.configs['CHALLENGE_CASES']

  def IsCorrect(self):
    """Returns whether this is correct solution."""
    return self.correct

  @taskgraph.task_method
  def Build(self, ui):
    """Build this solution."""
    if self.IsBuildCached():
      ui.console.PrintAction('COMPILE', self, 'up-to-date')
      yield True
    if not self.code.QUIET_COMPILE:
      ui.console.PrintAction('COMPILE', self)
    res = yield self.code.Compile()
    log = self.code.ReadCompileLog()
    if res.status != codes.RunResult.OK:
      ui.errors.Error(self, 'Compile Error (%s)' % res.status)
      ui.console.PrintLog(log)
      yield False
    if log:
      ui.console.Print('Compiler warnings found:')
      ui.console.PrintLog(log)
    if not self.SetCacheStamp(ui):
      yield False
    yield True

  @taskgraph.task_method
  def Run(self, args, cwd, input, output, timeout, precise):
    """Run this solution."""
    yield (yield self.code.Run(
        args=args, cwd=cwd, input=input, output=output,
        timeout=timeout, precise=precise))

  @taskgraph.task_method
  def Test(self, ui):
    """Run tests for the solution."""
    results = yield taskgraph.TaskBranch(
      [testset.TestSolution(self, ui) for testset in self.testsets])
    yield list(itertools.chain(*results))

  @taskgraph.task_method
  def Clean(self, ui):
    """Clean the solution."""
    ui.console.PrintAction('CLEAN', self)
    e = yield self.code.Clean()
    if e:
      ui.errors.Exception(self, e)
      yield False
    yield True


targets.registry.Add(Solution)
