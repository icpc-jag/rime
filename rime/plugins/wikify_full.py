#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import rime.basic.test  # NOQA
from rime.basic import test  # NOQA
from rime.core import commands as rime_commands  # NOQA
from rime.core import targets  # NOQA
from rime.core import taskgraph  # NOQA
import rime.plugins.wikify  # NOQA

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


def GetFileComment(dir, filename):
    filepath = os.path.join(dir, filename)
    if os.path.exists(filepath):
        f = open(filepath)
        r = f.read()
        f.close()
        return SafeUnicode(r).replace('\n', '&br;').replace('|', '&#x7c;')
    else:
        return ''


class Project(targets.registry.Project):
    @taskgraph.task_method
    def WikifyFull(self, ui):
        if not self.wikify_config_defined:
            ui.errors.Error(self, 'wikify_config() is not defined.')
            yield None
        wikiFull = yield self._GenerateWikiFull(ui)
        self._UploadWiki(wikiFull, ui)
        yield None

    @taskgraph.task_method
    def _GenerateWikiFull(self, ui):
        if not ui.options.skip_clean:
            yield self.Clean(ui)

        # Get system information.
        rev = SafeUnicode(builtin_commands.getoutput(
            'git show -s --oneline').replace('\n', ' ').replace('\r', ' '))
        username = getpass.getuser()
        hostname = socket.gethostname()

        # Generate content.
        wiki = u'** Summary\n'
        wiki += u'|||CENTER:|CENTER:|CENTER:|CENTER:|CENTER:|c\n'
        wiki += u'|~問題|~担当|~解答|~入力|~出力|~入検|~出検|\n'

        wikiFull = u'** Detail\n'

        results = yield taskgraph.TaskBranch([
            self._GenerateWikiFullOne(problem, ui)
            for problem in self.problems])
        (wikiResults, wikiFullResults) = zip(*results)
        wiki += ''.join(wikiResults)
        wikiFull += ''.join(wikiFullResults)

        cc = os.getenv('CC', 'gcc')
        cxx = os.getenv('CXX', 'g++')
        java_home = os.getenv('JAVA_HOME')
        if java_home is not None:
            java = os.path.join(java_home, 'bin/java')
            javac = os.path.join(java_home, 'bin/javac')
        else:
            java = 'java'
            javac = 'javac'
        environments = '** Environments\n'
        environments += (
            ':gcc:|' + builtin_commands.getoutput(
                '{0} --version'.format(cc)) + '\n')
        environments += (
            ':g++:|' + builtin_commands.getoutput(
                '{0} --version'.format(cxx)) + '\n')
        environments += (
            ':javac:|' + builtin_commands.getoutput(
                '{0} -version'.format(javac)) + '\n')
        environments += (
            ':java:|' + builtin_commands.getoutput(
                '{0} -version'.format(java)) + '\n')

        errors = '** Error Messages\n'
        if ui.errors.HasError():
            errors += ':COLOR(red):ERROR:|\n'
            for e in ui.errors.errors:
                errors += '--' + e + '\n'
        if ui.errors.HasWarning():
            errors += ':COLOR(yellow):WARNING:|\n'
            for e in ui.errors.warnings:
                errors += '--' + e + '\n'
        errors = SafeUnicode(errors)

        yield (u'#contents\n' +
               (u'このセクションは wikify_full plugin により自動生成されています '
                u'(rev.%(rev)s, uploaded by %(username)s @ %(hostname)s)\n' %
                {'rev': rev, 'username': username, 'hostname': hostname}
                ) + wiki + environments + errors + wikiFull)

    @taskgraph.task_method
    def _GenerateWikiFullOne(self, problem, ui):
        yield problem.Build(ui)

        # Get status.
        title = SafeUnicode(problem.title) or 'No Title'
        wiki_name = SafeUnicode(problem.wiki_name) or 'No Wiki Name'
        assignees = problem.assignees
        if isinstance(assignees, list):
            assignees = ','.join(assignees)
        assignees = SafeUnicode(assignees)

        # Get various information about the problem.
        wikiFull = '***' + title + '\n'
        solutions = sorted(problem.solutions, key=lambda x: x.name)
        solutionnames = [solution.name for solution in solutions]
        captions = [name.replace('-', ' ').replace('_', ' ')
                    for name in solutionnames]
        wikiFull += '|CENTER:~' + '|CENTER:~'.join(
            ['testcase', 'in', 'diff', 'md5'] + captions +
            ['Comments']) + '|h\n'
        formats = ['RIGHT:' for solution in solutions]
        wikiFull += '|' + '|'.join(
            ['LEFT:', 'RIGHT:', 'RIGHT:', 'LEFT:'] + formats +
            ['LEFT:']) + '|c\n'

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
                '|' +
                '|'.join(
                    [
                        casename.replace('_', ' ').replace('-', ' '),
                        GetFileSize(dir, casename + consts.IN_EXT),
                        GetFileSize(dir, casename + consts.DIFF_EXT),
                        GetFileHash(dir, casename + consts.IN_EXT)
                    ] +
                    [self._GetMessage(*t) for t in cols] +
                    [GetFileComment(dir, casename + '.comment')]
                ) +
                '|\n')
        wikiFull += ''.join(rows)

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
            cell_solutions = BGCOLOR_GOOD
        elif num_corrects >= 1:
            cell_solutions = BGCOLOR_NOTBAD
        else:
            cell_solutions = BGCOLOR_BAD
        cell_solutions += '%d+%d' % (num_corrects, num_incorrects)

        # Input:
        if num_tests >= 20:
            cell_input = BGCOLOR_GOOD + str(num_tests)
        else:
            cell_input = BGCOLOR_BAD + str(num_tests)

        # Output:
        if num_corrects >= 2 and num_agreed == num_corrects:
            cell_output = BGCOLOR_GOOD
        elif num_agreed >= 2:
            cell_output = BGCOLOR_NOTBAD
        else:
            cell_output = BGCOLOR_BAD
        cell_output += '%d/%d' % (num_agreed, num_corrects)

        # Validator:
        if problem.testset.validators:
            cell_validator = CELL_GOOD
        else:
            cell_validator = CELL_BAD

        # Judge:
        if need_custom_judge:
            custom_judges = [
                judge for judge in problem.testset.judges
                if judge.__class__ != basic_codes.InternalDiffCode]
            if custom_judges:
                cell_judge = CELL_GOOD
            else:
                cell_judge = CELL_BAD
        else:
            cell_judge = CELL_NA

        # Done.
        wiki = (u'|[[{}>{}]]|{}|{}|{}|{}|{}|{}|\n'.format(
            title, wiki_name, assignees, cell_solutions, cell_input,
            cell_output, cell_validator, cell_judge))

        yield (wiki, wikiFull)

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
        self.AddOptionEntry(rime_commands.OptionEntry(
            's', 'skip_clean', 'skip_clean', bool, False, None,
            'Skip cleaning generated files up.'
        ))

    def Run(self, obj, args, ui):
        if args:
            ui.console.PrintError(
                'Extra argument passed to wikify_full command!')
            return None

        if isinstance(obj, Project):
            return obj.WikifyFull(ui)

        ui.console.PrintError(
            'Wikify_full is not supported for the specified target.')
        return None


targets.registry.Override('Project', Project)

rime_commands.registry.Add(WikifyFull)
