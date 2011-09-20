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

import itertools
import os.path

from rime.core import targets
from rime.core import taskgraph
from rime.util import files


class Project(targets.registry.Project):
  """Project target."""

  CONFIG_FILENAME = 'PROJECT'

  def __init__(self, name, base_dir, parent):
    assert parent is None
    super(Project, self).__init__(name, base_dir, parent)
    self.project = self

  def PostLoad(self, ui):
    super(Project, self).PostLoad(ui)
    self._ChainLoad(ui)

  def _ChainLoad(self, ui):
    # Chain-load problems.
    self.problems = []
    for name in files.ListDir(self.base_dir):
      path = os.path.join(self.base_dir, name)
      if targets.registry.Problem.CanLoadFrom(path):
        problem = targets.registry.Problem(name, path, self)
        try:
          problem.Load(ui)
          self.problems.append(problem)
        except targets.ConfigurationError:
          ui.errors.Exception(problem)
    self.problems.sort(lambda a, b: cmp((a.id, a.name), (b.id, b.name)))

  def FindByBaseDir(self, base_dir):
    if self.base_dir == base_dir:
      return self
    for problem in self.problems:
      obj = problem.FindByBaseDir(base_dir)
      if obj:
        return obj
    return None

  @taskgraph.task_method
  def Build(self, ui):
    """Build all problems."""
    results = yield taskgraph.TaskBranch(
      [problem.Build(ui) for problem in self.problems])
    yield all(results)

  @taskgraph.task_method
  def Test(self, ui):
    """Run tests in the project."""
    results = yield taskgraph.TaskBranch(
      [problem.Test(ui) for problem in self.problems])
    yield list(itertools.chain(*results))

  @taskgraph.task_method
  def Clean(self, ui):
    """Clean the project."""
    results = yield taskgraph.TaskBranch(
      [problem.Clean(ui) for problem in self.problems])
    yield all(results)


targets.registry.Override('Project', Project)
