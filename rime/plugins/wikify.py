#!/usr/bin/python
# -*- coding: utf-8 -*-

import getpass
import re
import socket
import sys

from six.moves import urllib

from rime.basic import codes as basic_codes
import rime.basic.targets.problem
import rime.basic.targets.project  # NOQA
from rime.core import commands as rime_commands
from rime.core import targets
from rime.core import taskgraph

if sys.version_info[0] == 2:
    import commands as builtin_commands  # NOQA
else:
    import subprocess as builtin_commands


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


class Project(targets.registry.Project):
    def PreLoad(self, ui):
        super(Project, self).PreLoad(ui)
        self.wikify_config_defined = False

        def _wikify_config(url, page, encoding="utf-8", auth_realm=None,
                           auth_username=None, auth_password=None):
            self.wikify_config_defined = True
            self.wikify_url = url
            self.wikify_page = page
            self.wikify_encoding = encoding
            self.wikify_auth_realm = auth_realm
            self.wikify_auth_username = auth_username
            self.wikify_auth_password = auth_password
        self.exports['wikify_config'] = _wikify_config

    @taskgraph.task_method
    def Wikify(self, ui):
        if not self.wikify_config_defined:
            ui.errors.Error(self, 'wikify_config() is not defined.')
            yield None
        wiki = yield self._GenerateWiki(ui)
        self._UploadWiki(wiki, ui)
        yield None

    @taskgraph.task_method
    def _GenerateWiki(self, ui):
        if not ui.options.skip_clean:
            yield self.Clean(ui)

        # Get system information.
        rev = builtin_commands.getoutput('svnversion')
        username = getpass.getuser()
        hostname = socket.gethostname()
        # Generate content.
        wiki = (u'このセクションは wikify plugin により自動生成されています '
                u'(rev.%(rev)s, uploaded by %(username)s @ %(hostname)s)\n' %
                {'rev': rev, 'username': username, 'hostname': hostname})
        wiki += u'|||CENTER:|CENTER:|CENTER:|CENTER:|CENTER:|c\n'
        wiki += u'|~問題|~担当|~解答|~入力|~出力|~入検|~出検|\n'
        results = yield taskgraph.TaskBranch([
            self._GenerateWikiOne(problem, ui)
            for problem in self.problems])
        wiki += ''.join(results)
        yield wiki

    @taskgraph.task_method
    def _GenerateWikiOne(self, problem, ui):
        # Get status.
        title = SafeUnicode(problem.title) or 'No Title'
        wiki_name = SafeUnicode(problem.wiki_name) or 'No Wiki Name'
        assignees = problem.assignees
        if isinstance(assignees, list):
            assignees = ','.join(assignees)
        assignees = SafeUnicode(assignees)
        # Fetch test results.
        results = yield problem.Test(ui)
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
        yield (u'|[[{}>{}]]|{}|{}|{}|{}|{}|{}|\n'.format(
            title, wiki_name, assignees, cell_solutions, cell_input,
            cell_output, cell_validator, cell_judge))

    def _UploadWiki(self, wiki, ui):
        url = self.wikify_url
        page = SafeUnicode(self.wikify_page)
        encoding = self.wikify_encoding
        auth_realm = SafeUnicode(self.wikify_auth_realm)
        auth_username = self.wikify_auth_username
        auth_password = self.wikify_auth_password
        auth_hostname = urllib.parse.urlparse(url).hostname

        native_page = page.encode(encoding)
        native_wiki = wiki.encode(encoding)

        if self.wikify_auth_realm:
            auth_handler = urllib.request.HTTPBasicAuthHandler()
            auth_handler.add_password(
                auth_realm, auth_hostname, auth_username, auth_password)
            opener = urllib.request.build_opener(auth_handler)
            urllib.request.install_opener(opener)

        ui.console.PrintAction('UPLOAD', None, url)

        edit_params = {
            'cmd': 'edit',
            'page': native_page,
        }
        edit_page_content = urllib.request.urlopen(
            '%s?%s' % (url, urllib.parse.urlencode(edit_params))).read()

        digest = re.search(
            r'value="([0-9a-f]{32})"',
            edit_page_content.decode(encoding)).group(1)

        update_params = {
            'cmd': 'edit',
            'page': native_page,
            'digest': digest,
            'msg': native_wiki,
            'write': u'ページの更新'.encode(encoding),
            'encode_hint': u'ぷ'.encode(encoding),
        }
        urllib.request.urlopen(
            url, urllib.parse.urlencode(update_params).encode(encoding))


class Problem(targets.registry.Problem):
    def PreLoad(self, ui):
        super(Problem, self).PreLoad(ui)
        base_problem = self.exports['problem']

        def _problem(wiki_name, assignees, need_custom_judge, **kwargs):
            self.wiki_name = wiki_name
            self.assignees = assignees
            self.need_custom_judge = need_custom_judge
            return base_problem(**kwargs)
        self.exports['problem'] = _problem


class Wikify(rime_commands.CommandBase):
    def __init__(self, parent):
        super(Wikify, self).__init__(
            'wikify',
            '',
            'Upload test results to Pukiwiki. (wikify plugin)',
            '',
            parent)
        self.AddOptionEntry(rime_commands.OptionEntry(
            's', 'skip_clean', 'skip_clean', bool, False, None,
            'Skip cleaning generated files up.'
        ))

    def Run(self, obj, args, ui):
        if args:
            ui.console.PrintError('Extra argument passed to wikify command!')
            return None

        if isinstance(obj, Project):
            return obj.Wikify(ui)

        ui.console.PrintError(
            'Wikify is not supported for the specified target.')
        return None


targets.registry.Override('Project', Project)
targets.registry.Override('Problem', Problem)

rime_commands.registry.Add(Wikify)
