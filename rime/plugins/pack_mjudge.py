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
import os
import os.path

import rime.basic.targets.problem  # target dependency
import rime.basic.targets.project  # target dependency
import rime.basic.targets.testset  # target dependency
from rime.basic import consts
from rime.core import commands
from rime.core import targets
from rime.core import taskgraph
from rime.util import files


_PACKED_TARBALL_TEMPLATE = '%s.tar.gz'


class Project(targets.registry.Project):
  @taskgraph.task_method
  def Pack(self, ui):
    results = yield taskgraph.TaskBranch(
      [problem.Pack(ui) for problem in self.problems])
    yield all(results)


class Problem(targets.registry.Problem):
  @taskgraph.task_method
  def Pack(self, ui):
    results = yield taskgraph.TaskBranch(
      [testset.Pack(ui) for testset in self.testsets])
    yield all(results)


class Testset(targets.registry.Testset):
  def __init__(self, *args, **kwargs):
    super(Testset, self).__init__(*args, **kwargs)
    self.pack_dir = os.path.join(self.out_dir, 'pack')

  @taskgraph.task_method
  def Pack(self, ui):
    if not (yield self.Build(ui)):
      yield False
    testcases = self.ListTestCases()
    ui.console.PrintAction('PACK', self, progress=True)
    try:
      files.RemoveTree(self.pack_dir)
      files.MakeDir(self.pack_dir)
    except:
      ui.errors.Exception(self)
      yield False
    for (i, testcase) in enumerate(testcases):
      basename = os.path.splitext(testcase.infile)[0]
      difffile = basename + consts.DIFF_EXT
      packed_infile = str(i+1) + consts.IN_EXT
      packed_difffile = str(i+1) + consts.DIFF_EXT
      try:
        ui.console.PrintAction(
          'PACK',
          self,
          '%s -> %s' % (testcase.infile, packed_infile),
          progress=True)
        files.CopyFile(os.path.join(self.out_dir, testcase.infile),
                       os.path.join(self.pack_dir, packed_infile))
        ui.console.PrintAction(
          'PACK',
          self,
          '%s -> %s' % (difffile, packed_difffile),
          progress=True)
        files.CopyFile(os.path.join(self.out_dir, difffile),
                       os.path.join(self.pack_dir, packed_difffile))
      except:
        ui.errors.Exception(self)
        yield False
    tarball_filename = _PACKED_TARBALL_TEMPLATE % self.name
    tar_args = ('tar', 'czf',
                os.path.join(os.pardir, os.pardir, tarball_filename),
                os.curdir)
    ui.console.PrintAction(
      'PACK',
      self,
      ' '.join(tar_args),
      progress=True)
    devnull = files.OpenNull()
    task = taskgraph.ExternalProcessTask(
      tar_args, cwd=self.pack_dir,
      stdin=devnull, stdout=devnull, stderr=devnull)
    try:
      proc = yield task
    except:
      ui.errors.Exception(self)
      yield False
    ret = proc.returncode
    if ret != 0:
      ui.errors.Error(self, 'tar failed: ret = %d' % ret)
      yield False
    ui.console.PrintAction(
      'PACK',
      self,
      tarball_filename)
    yield True


targets.registry.Override('Project', Project)
targets.registry.Override('Problem', Problem)
targets.registry.Override('Testset', Testset)


class Pack(commands.CommandBase):
  def __init__(self, parent):
    super(Pack, self).__init__(
      'pack',
      '',
      'Pack testsets to export to M-judge. (pack_mjudge plugin)',
      '',
      parent)

  def Run(self, obj, args, ui):
    """Entry point for pack command."""
    if args:
      ui.console.PrintError('Extra argument passed to pack command!')
      return None

    if isinstance(obj, (Project, Problem, Testset)):
      return obj.Pack(ui)

    ui.console.PrintError('Pack is not supported for the specified target.')
    return None

commands.registry.Add(Pack)
