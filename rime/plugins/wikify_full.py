#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Rime Project.
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

import commands as builtin_commands
import getpass
import itertools
import os.path
import re
import socket
import subprocess
import urllib
import urllib2
import urlparse

from rime.basic.targets import problem
import rime.basic.targets.project  # target dependency
import rime.basic.test
from rime.basic import codes as basic_codes
from rime.basic import consts
from rime.basic import test
from rime.core import codes as core_codes
from rime.core import commands as rime_commands
from rime.core import targets
from rime.core import taskgraph
import rime.plugins.wikify  # target dependency
from rime.util import files

BGCOLOR_TITLE = 'BGCOLOR(#eeeeee):'
BGCOLOR_GOOD = 'BGCOLOR(#ccffcc):'
BGCOLOR_NOTBAD = 'BGCOLOR(#ffffcc):'
BGCOLOR_BAD = 'BGCOLOR(#ffcccc):'
BGCOLOR_NA = 'BGCOLOR(#cccccc):'

CELL_GOOD = BGCOLOR_GOOD + '&#x25cb;'
CELL_NOTBAD = BGCOLOR_NOTBAD + '&#x25b3;'
CELL_BAD = BGCOLOR_BAD + '&#xd7;'
CELL_NA = BGCOLOR_NA + '-'


def SafeUnicode(s):
  if not isinstance(s, unicode):
    s = s.decode('utf-8')
  return s


class Project(targets.registry.Project):
  @taskgraph.task_method
  def WikifyFull(self, ui):
    if not self.wikify_config_defined:
      ui.errors.Error(self, 'wikify_config() is not defined.')
      yield None
    wiki = yield self._GenerateWikiFull(ui)
    self._UploadWiki(wiki, ui)
    yield None

  @taskgraph.task_method
  def _GenerateWikiFull(self, ui):
    yield self.Clean(ui) # 重すぎるときはコメントアウト
    # Get system information.
    rev = builtin_commands.getoutput('svnversion')
    username = getpass.getuser()
    hostname = socket.gethostname()
    # Generate content.
    wiki = (u'#contents\n'
            u'このセクションは wikify_full plugin により自動生成されています '
            u'(rev.%(rev)s, uploaded by %(username)s @ %(hostname)s)\n' % 
            {'rev': rev, 'username': username, 'hostname': hostname})
    results = yield taskgraph.TaskBranch([
        self._GenerateWikiFullOne(problem, ui)
        for problem in self.problems])
    wiki += ''.join(results)
    yield wiki

  @taskgraph.task_method
  def _GenerateWikiFullOne(self, problem, ui):
    yield problem.Build(ui)

    # Get status.
    title = SafeUnicode(problem.title) or 'No Title'
    # Get various information about the problem.
    wiki = '***' + title + '\n'
    solutions = sorted(problem.solutions, key=lambda x: x.name)
    solutionnames = [solution.name for solution in solutions]
    wiki += '|~' + '|~'.join(['testcase'] + solutionnames) + '|h\n'

    dics = {}
    for testcase in problem.testset.ListTestCases():
      testname = os.path.splitext(os.path.basename(testcase.infile))[0]
      dics[testname] = {}
    for solution in solutions:
      name = solution.name
      test_result = (yield problem.testset.TestSolution(solution, ui))[0]
      for (testcase, result) in test_result.results.items():
        testname = os.path.splitext(os.path.basename(testcase.infile))[0]
        dics.setdefault(testname, {})[name] = (result.verdict, result.time)
    testnames = sorted(dics.keys())
    lists = []
    for testname in testnames:
      cols = []
      for name in solutionnames:
        cols.append(dics[testname].get(name, (test.TestCaseResult.NA, None)))
      lists.append((testname, cols))
    rows = []
    for casename, cols in lists:
      rows.append(
          '|' +
          '|'.join([casename] + [self._GetMessage(*t) for t in cols]) +
          '|\n')
    wiki += ''.join(rows)

    yield wiki

  def _GetMessage(self, verdict, time):
    if verdict is test.TestCaseResult.NA:
      return BGCOLOR_NA + str(verdict)
    elif time is None:
      return BGCOLOR_BAD + str(verdict)
    else:
      return BGCOLOR_GOOD + '%.2fs' % (time)


class WikifyFull(rime_commands.CommandBase):
  def __init__(self, parent):
    super(WikifyFull, self).__init__(
        'wikify_full',
        '',
        'Upload all test results to Pukiwiki. (wikify_full plugin)',
        '',
        parent)

  def Run(self, obj, args, ui):
    if args:
      ui.console.PrintError('Extra argument passed to wikify_full command!')
      return None

    if isinstance(obj, Project):
      return obj.WikifyFull(ui)

    ui.console.PrintError('Wikify_full is not supported for the specified target.')
    return None


targets.registry.Override('Project', Project)

rime_commands.registry.Add(WikifyFull)

