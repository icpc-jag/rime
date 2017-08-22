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

import codecs
import commands as builtin_commands
import getpass
import hashlib
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
from rime.util import files

HTMLIFY_BGCOLOR_GOOD = ' class="success">'
HTMLIFY_BGCOLOR_NOTBAD = ' class="warning">'
HTMLIFY_BGCOLOR_BAD = ' class="danger">'
HTMLIFY_BGCOLOR_NA = ' class="info">'

HTMLIFY_CELL_GOOD = HTMLIFY_BGCOLOR_GOOD + '&#x25cb;'
HTMLIFY_CELL_NOTBAD = HTMLIFY_BGCOLOR_NOTBAD + '&#x25b3;'
HTMLIFY_CELL_BAD = HTMLIFY_BGCOLOR_BAD + '&#xd7;'
HTMLIFY_CELL_NA = HTMLIFY_BGCOLOR_NA + '-'


def SafeUnicode(s):
  if not isinstance(s, unicode):
    s = s.decode('utf-8')
  return s


def GetFileSize(dir, filename):
  filepath = os.path.join(dir, filename)
  if os.path.exists(filepath):
    return '%dB' % os.path.getsize(filepath)
  else:
    return '-'


def GetFileHash(dir, filename):
  filepath = os.path.join(dir, filename)
  if os.path.exists(filepath):
    f = open(filepath)
    r = f.read()
    f.close()
    return hashlib.md5(SafeUnicode(r)).hexdigest()
  else:
    return ''


def GetHtmlifyFileComment(dir, filename):
  filepath = os.path.join(dir, filename)
  if os.path.exists(filepath):
    f = open(filepath)
    r = f.read().strip()
    f.close()
    return SafeUnicode(r).replace('\n', '<br>')
  else:
    return ''


class Project(targets.registry.Project):
  @taskgraph.task_method
  def HtmlifyFull(self, ui):
    htmlFull = yield self._GenerateHtmlFull(ui)
    codecs.open("summary.html", 'w', 'utf8').write(htmlFull)
    yield None

  @taskgraph.task_method
  def _GenerateHtmlFull(self, ui):
    #yield self.Clean(ui) # 重すぎるときはコメントアウト

    # Get system information.
    rev = SafeUnicode(builtin_commands.getoutput('git show -s --oneline').replace('\n', ' ').replace('\r', ' '))
    username = getpass.getuser()
    hostname = socket.gethostname()

    header  = u'<!DOCTYPE html>\n<html lang="ja"><head>'
    header += u'<link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css"></head>\n<body>'
    info    = u'このセクションは htmlfy_full plugin により自動生成されています '
    info   += (u'(rev.%(rev)s, uploaded by %(username)s @ %(hostname)s)\n' % {'rev': rev, 'username': username, 'hostname': hostname})
    footer  = u'</body></html>'

    # Generate content.
    html =  u'<h2>Summary</h2>\n<table class="table">\n'
    html += u'<thead><tr><th>問題</th><th>担当</th><th>解答</th><th>入力</th><th>出力</th><th>入検</th><th>出検</th></tr></thead>\n'

    htmlFull =  u'<h2>Detail<h2>\n'

    results = yield taskgraph.TaskBranch([
        self._GenerateHtmlFullOne(problem, ui)
        for problem in self.problems])
    (htmlResults, htmlFullResults) = zip(*results)
    html += '<tbody>' + ''.join(htmlResults) + '</tbody></table>\n'
    htmlFull += ''.join(htmlFullResults)

    environments =  '<h2>Environments</h2>\n<dl class="dl-horizontal">\n'
    environments += '<dt>gcc:</dt><dd>'   + builtin_commands.getoutput('gcc --version')  + '</dd>\n'
    environments += '<dt>g++:</dt><dd>'   + builtin_commands.getoutput('g++ --version')  + '</dd>\n'
    environments += '<dt>javac:</dt><dd>' + builtin_commands.getoutput('javac -version') + '</dd>\n'
    environments += '<dt>java:</dt><dd>'  + builtin_commands.getoutput('java -version')  + '</dd>\n'
    environments += '</dl>\n'

    errors = ''
    if ui.errors.HasError() or ui.errors.HasWarning():
      errors = '<h2>Error Messages</h2>\n<dl class="dl-horizontal">\n'
      if ui.errors.HasError():
        errors += '<dt class="danger">ERROR:</dt><dd><ul>\n'
        for e in ui.errors.errors:
          errors += '<li>' + e + '</li>\n'
        errors += '</ul></dt>\n'
      if ui.errors.HasWarning():
        errors += '<dt class="warning">WARNING:</dt><dd><ul>\n'
        for e in ui.errors.warnings:
          errors += '<li>' + e + '</li>\n'
        errors += '</ul></dd>\n'
      errors += '</dl>\n'

    yield header + info + html + environments + errors + htmlFull + footer

  @taskgraph.task_method
  def _GenerateHtmlFullOne(self, problem, ui):
    yield problem.Build(ui)

    # Get status.
    title = SafeUnicode(problem.title) or 'No Title'
    assignees = problem.assignees
    if isinstance(assignees, list):
      assignees = ','.join(assignees)
    assignees = SafeUnicode(assignees)

    # Get various information about the problem.
    htmlFull = '<h3>' + title + '</h3>\n'
    solutions = sorted(problem.solutions, key=lambda x: x.name)
    solutionnames = [solution.name for solution in solutions]

    captions = [name.replace('-', ' ').replace('_', ' ') for name in solutionnames]
    htmlFull += '<table class="table">\n<thead><tr><th>' + '</th><th>'.join(['testcase', 'in', 'diff', 'md5'] + captions + ['Comments']) + '</th></tr></thead>\n<tbody>\n'
    #formats = ['RIGHT:' for solution in solutions]
    #htmlFull += '|' + '|'.join(['LEFT:', 'RIGHT:', 'RIGHT:', 'LEFT:'] + formats + ['LEFT:']) + '|c\n'

    dics = {}
    for testcase in problem.testset.ListTestCases():
      testname = os.path.splitext(os.path.basename(testcase.infile))[0]
      dics[testname] = {}
    results = []
    for solution in solutions:
      name = solution.name
      test_result = (yield problem.testset.TestSolution(solution, ui))[0]
      results.append(test_result)
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
    dir = problem.testset.out_dir
    for casename, cols in lists:
      rows.append(
          '<tr><td' +
          '</td><td'.join(
            [
              '>' + casename.replace('_', ' ').replace('-', ' '),
              '>' + GetFileSize(dir, casename + consts.IN_EXT),
              '>' + GetFileSize(dir, casename + consts.DIFF_EXT),
              '>' + GetFileHash(dir, casename + consts.IN_EXT)
            ]
            + [self._GetHtmlifyMessage(*t) for t in cols]
            + ['>' + GetHtmlifyFileComment(dir, casename + '.comment')]
            ) +
          '</td></tr>\n')
    htmlFull += ''.join(rows)
    htmlFull += '</tbody></table>'

    # Fetch test results.
    #results = yield problem.Test(ui)

    # Get various information about the problem.
    num_solutions = len(results)
    num_tests = len(problem.testset.ListTestCases())
    correct_solution_results = [result for result in results
                                if result.solution.IsCorrect()]
    num_corrects = len(correct_solution_results)
    num_incorrects = num_solutions - num_corrects
    num_agreed = len([result for result in correct_solution_results
                      if result.expected])
    need_custom_judge = problem.need_custom_judge

    # Solutions:
    if num_corrects >= 2:
      cell_solutions = HTMLIFY_BGCOLOR_GOOD
    elif num_corrects >= 1:
      cell_solutions = HTMLIFY_BGCOLOR_NOTBAD
    else:
      cell_solutions = HTMLIFY_BGCOLOR_BAD
    cell_solutions += '%d+%d' % (num_corrects, num_incorrects)

    # Input:
    if num_tests >= 20:
      cell_input = HTMLIFY_BGCOLOR_GOOD + str(num_tests)
    else:
      cell_input = HTMLIFY_BGCOLOR_BAD + str(num_tests)

    # Output:
    if num_corrects >= 2 and num_agreed == num_corrects:
      cell_output = HTMLIFY_BGCOLOR_GOOD
    elif num_agreed >= 2:
      cell_output = HTMLIFY_BGCOLOR_NOTBAD
    else:
      cell_output = HTMLIFY_BGCOLOR_BAD
    cell_output += '%d/%d' % (num_agreed, num_corrects)

    # Validator:
    if problem.testset.validators:
      cell_validator = HTMLIFY_CELL_GOOD
    else:
      cell_validator = HTMLIFY_CELL_BAD

    # Judge:
    if need_custom_judge:
      custom_judges = [judge for judge in problem.testset.judges
                       if judge.__class__ != basic_codes.InternalDiffCode]
      if custom_judges:
        cell_judge = HTMLIFY_CELL_GOOD
      else:
        cell_judge = HTMLIFY_CELL_BAD
    else:
      cell_judge = HTMLIFY_CELL_NA

    # Done.
    html = (('<tr><td>%(title)s</td><td>%(assignees)s</td><td'
            '%(cell_solutions)s</td><td%(cell_input)s</td><td%(cell_output)s</td><td'
            '%(cell_validator)s</td><td%(cell_judge)s<td></tr>\n') % locals())

    yield (html, htmlFull)

  def _GetHtmlifyMessage(self, verdict, time):
    if verdict is test.TestCaseResult.NA:
      return HTMLIFY_BGCOLOR_NA + str(verdict)
    elif time is None:
      return HTMLIFY_BGCOLOR_BAD + str(verdict)
    else:
      return HTMLIFY_BGCOLOR_GOOD + '%.2fs' % (time)


class HtmlifyFull(rime_commands.CommandBase):
  def __init__(self, parent):
    super(HtmlifyFull, self).__init__(
        'htmlify_full',
        '',
        'Local version of htmlfy_full. (htmlify_full plugin)',
        '',
        parent)

  def Run(self, obj, args, ui):
    if args:
      ui.console.PrintError('Extra argument passed to htmlify_full command!')
      return None

    if isinstance(obj, Project):
      return obj.HtmlifyFull(ui)

    ui.console.PrintError('Htmlify_full is not supported for the specified target.')
    return None


targets.registry.Override('Project', Project)

rime_commands.registry.Add(HtmlifyFull)

