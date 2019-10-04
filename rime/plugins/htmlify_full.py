#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import getpass
import hashlib
import os
import os.path
import socket
import sys

if sys.version_info[0] == 2:
    import commands as builtin_commands  # NOQA
else:
    import subprocess as builtin_commands

from rime.basic import codes as basic_codes  # NOQA
from rime.basic import consts  # NOQA
import rime.basic.targets.project  # NOQA
from rime.basic import test  # NOQA
from rime.core import commands as rime_commands  # NOQA
from rime.core import targets  # NOQA
from rime.core import taskgraph  # NOQA

HTMLIFY_BGCOLOR_GOOD = ' class="success">'
HTMLIFY_BGCOLOR_NOTBAD = ' class="warning">'
HTMLIFY_BGCOLOR_BAD = ' class="danger">'
HTMLIFY_BGCOLOR_NA = ' class="info">'

HTMLIFY_CELL_GOOD = HTMLIFY_BGCOLOR_GOOD + '&#x25cb;'
HTMLIFY_CELL_NOTBAD = HTMLIFY_BGCOLOR_NOTBAD + '&#x25b3;'
HTMLIFY_CELL_BAD = HTMLIFY_BGCOLOR_BAD + '&#xd7;'
HTMLIFY_CELL_NA = HTMLIFY_BGCOLOR_NA + '-'


def SafeUnicode(s):
    if sys.version_info.major == 2 and not isinstance(s, unicode):  # NOQA
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
        return hashlib.md5(SafeUnicode(r).encode('utf-8')).hexdigest()
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
        if not ui.options.skip_clean:
            yield self.Clean(ui)

        # Get system information.
        rev = SafeUnicode(builtin_commands.getoutput(
            'git show -s --oneline').replace('\n', ' ').replace('\r', ' '))
        username = getpass.getuser()
        hostname = socket.gethostname()

        header = u'<!DOCTYPE html>\n<html lang="ja"><head>'
        header += (
            u'<meta charset="utf-8"/>'
            '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com'
            '/bootstrap/3.2.0/css/bootstrap.min.css"></head>\n<body>')
        info = u'このセクションは htmlify_full plugin により自動生成されています '
        info += (u'(rev.%(rev)s, uploaded by %(username)s @ %(hostname)s)\n'
                 % {'rev': rev, 'username': username, 'hostname': hostname})
        footer = u'</body></html>'

        # Generate content.
        html = u'<h2>Summary</h2>\n<table class="table">\n'
        html += (u'<thead><tr><th>問題</th><th>担当</th><th>解答</th><th>入力</th>'
                 u'<th>出力</th><th>入検</th><th>出検</th></tr></thead>\n')

        htmlFull = u'<h2>Detail</h2>\n'

        results = yield taskgraph.TaskBranch([
            self._GenerateHtmlFullOne(problem, ui)
            for problem in self.problems])
        (htmlResults, htmlFullResults) = zip(*results)
        html += '<tbody>' + ''.join(htmlResults) + '</tbody></table>\n'
        htmlFull += ''.join(htmlFullResults)

        cc = os.getenv('CC', 'gcc')
        cxx = os.getenv('CXX', 'g++')
        java_home = os.getenv('JAVA_HOME')
        if java_home is not None:
            java = os.path.join(java_home, 'bin/java')
            javac = os.path.join(java_home, 'bin/javac')
        else:
            java = 'java'
            javac = 'javac'
        environments = '<h2>Environments</h2>\n<dl class="dl-horizontal">\n'
        environments += (
            '<dt>gcc:</dt><dd>' +
            builtin_commands.getoutput('{0} --version'.format(cc)) +
            '</dd>\n')
        environments += (
            '<dt>g++:</dt><dd>' +
            builtin_commands.getoutput('{0} --version'.format(cxx)) +
            '</dd>\n')
        environments += (
            '<dt>javac:</dt><dd>' +
            builtin_commands.getoutput('{0} -version'.format(javac)) +
            '</dd>\n')
        environments += (
            '<dt>java:</dt><dd>' +
            builtin_commands.getoutput('{0} -version'.format(java)) +
            '</dd>\n')
        environments += '</dl>\n'

        errors = ''
        if ui.errors.HasError() or ui.errors.HasWarning():
            errors = '<h2>Error Messages</h2>\n<dl class="dl-horizontal">\n'
            if ui.errors.HasError():
                errors += '<dt class="danger">ERROR:</dt><dd><ul>\n'
                for e in ui.errors.errors:
                    errors += '<li>' + e + '</li>\n'
                errors += '</ul></dd>\n'
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

        captions = [
            name.replace('-', ' ').replace('_', ' ') for name in solutionnames]
        htmlFull += ('<table class="table">\n<thead><tr><th>' +
                     '</th><th>'.join(
                         ['testcase', 'in', 'diff', 'md5'] + captions +
                         ['Comments']) + '</th></tr></thead>\n<tbody>\n')

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
                testname = os.path.splitext(
                    os.path.basename(testcase.infile))[0]
                dics.setdefault(testname, {})[name] = (
                    result.verdict, result.time)
        testnames = sorted(dics.keys())
        lists = []
        for testname in testnames:
            cols = []
            for name in solutionnames:
                cols.append(dics[testname].get(
                    name, (test.TestCaseResult.NA, None)))
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
                    ] +
                    [self._GetHtmlifyMessage(*t) for t in cols] +
                    ['>' + GetHtmlifyFileComment(dir, casename + '.comment')]
                ) +
                '</td></tr>\n')
        htmlFull += ''.join(rows)
        htmlFull += '</tbody></table>'

        # Fetch test results.
        # results = yield problem.Test(ui)

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
            custom_judges = [
                judge for judge in problem.testset.judges
                if judge.__class__ != basic_codes.InternalDiffCode]
            if custom_judges:
                cell_judge = HTMLIFY_CELL_GOOD
            else:
                cell_judge = HTMLIFY_CELL_BAD
        else:
            cell_judge = HTMLIFY_CELL_NA

        # Done.
        html = ('<tr><td>{}</td><td>{}</td><td{}</td><td{}</td>'
                '<td{}</td><td{}</td><td{}<td></tr>\n'.format(
                    title, assignees, cell_solutions, cell_input,
                    cell_output, cell_validator, cell_judge))

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
            'Local version of htmlify_full. (htmlify_full plugin)',
            '',
            parent)
        self.AddOptionEntry(rime_commands.OptionEntry(
            's', 'skip_clean', 'skip_clean', bool, False, None,
            'Skip cleaning generated files up.'
        ))

    def Run(self, obj, args, ui):
        if args:
            ui.console.PrintError(
                'Extra argument passed to htmlify_full command!')
            return None

        if isinstance(obj, Project):
            return obj.HtmlifyFull(ui)

        ui.console.PrintError(
            'Htmlify_full is not supported for the specified target.')
        return None


targets.registry.Override('Project', Project)

rime_commands.registry.Add(HtmlifyFull)
