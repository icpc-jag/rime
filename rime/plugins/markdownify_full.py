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

MARKDOWNIFY_EMOJI_GOOD = ' :white_check_mark: '
MARKDOWNIFY_EMOJI_NOTBAD = ' :large_blue_diamond: '
MARKDOWNIFY_EMOJI_BAD = ' :x: '
MARKDOWNIFY_EMOJI_NA = ' :wavy_dash: '


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


def GetMarkdownifyFileComment(dir, filename):
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
    def MarkdownifyFull(self, ui):
        markdownFull = yield self._GenerateMarkdownFull(ui)
        codecs.open("summary.md", 'w', 'utf8').write(markdownFull)
        yield None

    @taskgraph.task_method
    def _GenerateMarkdownFull(self, ui):
        # yield self.Clean(ui) # 重すぎるときはコメントアウト

        # Get system information.
        rev = SafeUnicode(builtin_commands.getoutput(
            'git show -s --oneline').replace('\n', ' ').replace('\r', ' '))
        username = getpass.getuser()
        hostname = socket.gethostname()

        header = u'# Project Status\n\n'
        info = u'このファイルは markdownify_full plugin により自動生成されています '
        info += (u'(rev.%(rev)s, uploaded by %(username)s @ %(hostname)s)\n\n'
                 % {'rev': rev, 'username': username, 'hostname': hostname})
        footer = u''

        # Generate content.
        markdown = u'## Summary\n\n'
        markdown += (
            u'問題|担当|解答|入力|出力|入検|出検\n'
            ':---|:---|:---|:---|:---|:---|:---\n'
            )

        markdownFull = u'## Detail\n\n'

        results = yield taskgraph.TaskBranch([
            self._GenerateMarkdownFullOne(problem, ui)
            for problem in self.problems])
        (markdownResults, markdownFullResults) = zip(*results)
        markdown += ''.join(markdownResults) + '\n'
        markdownFull += ''.join(markdownFullResults)

        cc = os.getenv('CC', 'gcc')
        cxx = os.getenv('CXX', 'g++')
        java_home = os.getenv('JAVA_HOME')
        if java_home is not None:
            java = os.path.join(java_home, 'bin/java')
            javac = os.path.join(java_home, 'bin/javac')
        else:
            java = 'java'
            javac = 'javac'
        environments = '## Environments\n\n'
        environments += (
            '- gcc\n\t- ' +
            builtin_commands.getoutput('{0} --version'.format(cc)) +
            '\n')
        environments += (
            '- g++\n\t- ' +
            builtin_commands.getoutput('{0} --version'.format(cxx)) +
            '\n')
        environments += (
            '- javac\n\t- ' +
            builtin_commands.getoutput('{0} -version'.format(javac)) +
            '\n')
        environments += (
            '- java\n\t- ' +
            builtin_commands.getoutput('{0} -version'.format(java)) +
            '\n')
        environments += '\n'

        errors = ''
        if ui.errors.HasError() or ui.errors.HasWarning():
            errors = '## Error Messages\n\n'
            if ui.errors.HasError():
                errors += '- ERROR:\n'
                for e in ui.errors.errors:
                    errors += '\t- ' + e + '\n'
            if ui.errors.HasWarning():
                errors += '- WARNING:\n'
                for e in ui.errors.warnings:
                    errors += '\t- ' + e + '\n'
            errors += '\n'

        yield (
            header + info + markdown + environments + errors + markdownFull
            + footer)

    @taskgraph.task_method
    def _GenerateMarkdownFullOne(self, problem, ui):
        yield problem.Build(ui)

        # Get status.
        title = SafeUnicode(problem.title) or 'No Title'
        assignees = problem.assignees
        if isinstance(assignees, list):
            assignees = ','.join(assignees)
        assignees = SafeUnicode(assignees)

        # Get various information about the problem.
        markdownFull = '### ' + title + '\n\n'
        solutions = sorted(problem.solutions, key=lambda x: x.name)
        solutionnames = [solution.name for solution in solutions]

        captions = [
            name.replace('-', ' ').replace('_', ' ') for name in solutionnames]
        markdownFull += ('|'.join(
                         ['testcase', 'in', 'diff', 'md5'] + captions +
                         ['Comments']) + '\n')
        markdownFull += '|:---' * (5 + len(captions)) + '\n'

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
                '|'.join(
                    [
                        casename.replace('_', ' ').replace('-', ' '),
                        GetFileSize(dir, casename + consts.IN_EXT),
                        GetFileSize(dir, casename + consts.DIFF_EXT),
                        '`%s`' % GetFileHash(dir, casename + consts.IN_EXT)[:7]
                    ] +
                    [self._GetMarkdownifyMessage(*t) for t in cols] +
                    [GetMarkdownifyFileComment(dir, casename + '.comment')]
                ) +
                '\n')
        markdownFull += ''.join(rows) + '\n'

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
            cell_solutions = MARKDOWNIFY_EMOJI_GOOD
        elif num_corrects >= 1:
            cell_solutions = MARKDOWNIFY_EMOJI_NOTBAD
        else:
            cell_solutions = MARKDOWNIFY_EMOJI_BAD
        cell_solutions += '%d+%d' % (num_corrects, num_incorrects)

        # Input:
        if num_tests >= 20:
            cell_input = MARKDOWNIFY_EMOJI_GOOD + str(num_tests)
        else:
            cell_input = MARKDOWNIFY_EMOJI_BAD + str(num_tests)

        # Output:
        if num_corrects >= 2 and num_agreed == num_corrects:
            cell_output = MARKDOWNIFY_EMOJI_GOOD
        elif num_agreed >= 2:
            cell_output = MARKDOWNIFY_EMOJI_NOTBAD
        else:
            cell_output = MARKDOWNIFY_EMOJI_BAD
        cell_output += '%d/%d' % (num_agreed, num_corrects)

        # Validator:
        if problem.testset.validators:
            cell_validator = MARKDOWNIFY_EMOJI_GOOD
        else:
            cell_validator = MARKDOWNIFY_EMOJI_BAD

        # Judge:
        if need_custom_judge:
            custom_judges = [
                judge for judge in problem.testset.judges
                if judge.__class__ != basic_codes.InternalDiffCode]
            if custom_judges:
                cell_judge = MARKDOWNIFY_EMOJI_GOOD
            else:
                cell_judge = MARKDOWNIFY_EMOJI_BAD
        else:
            cell_judge = MARKDOWNIFY_EMOJI_NA

        # Done.
        markdown = (u'{}|{}|{}|{}|{}|{}|{}\n'.format(
                    title, assignees, cell_solutions, cell_input,
                    cell_output, cell_validator, cell_judge))

        yield (markdown, markdownFull)

    def _GetMarkdownifyMessage(self, verdict, time):
        if verdict is test.TestCaseResult.NA:
            return MARKDOWNIFY_EMOJI_NA + str(verdict)
        elif time is None:
            return MARKDOWNIFY_EMOJI_BAD + str(verdict)
        else:
            return MARKDOWNIFY_EMOJI_GOOD + '%.2fs' % (time)


class MarkdownifyFull(rime_commands.CommandBase):
    def __init__(self, parent):
        super(MarkdownifyFull, self).__init__(
            'markdownify_full',
            '',
            'Markdownify full plugin',
            '',
            parent)

    def Run(self, obj, args, ui):
        if args:
            ui.console.PrintError(
                'Extra argument passed to markdownify_full command!')
            return None

        if isinstance(obj, Project):
            return obj.MarkdownifyFull(ui)

        ui.console.PrintError(
            'Markdownify_full is not supported for the specified target.')
        return None


targets.registry.Override('Project', Project)

rime_commands.registry.Add(MarkdownifyFull)
