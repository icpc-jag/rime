#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import re
import sys

from six.moves import urllib

import rime.basic.targets.problem
import rime.basic.targets.project  # NOQA
from rime.core import commands as rime_commands
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.summary import summary


def SafeUnicode(s):
    if sys.version_info.major == 2 and not isinstance(s, unicode):  # NOQA
        s = s.decode('utf-8')
    return s


class Project(targets.registry.Project):
    def PreLoad(self, ui):
        super(Project, self).PreLoad(ui)
        self.wikify_config_defined = False
        self._Summarize = summary.GenerateSummary

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

        if not ui.options.skip_clean:
            yield self.Clean(ui)

        results = yield self.Test(ui)
        template_file = os.path.join(
            os.path.dirname(__file__),
            'summary',
            'pukiwiki.ninja')
        content = self._Summarize(results, template_file, ui)
        self._UploadWiki(content, ui)
        yield None

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
