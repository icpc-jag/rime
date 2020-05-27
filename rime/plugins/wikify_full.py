#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path

import rime.basic.targets.project  # NOQA
from rime.core import commands as rime_commands  # NOQA
from rime.core import targets  # NOQA
from rime.core import taskgraph  # NOQA


class Project(targets.registry.Project):
    @taskgraph.task_method
    def WikifyFull(self, ui):
        if not self.wikify_config_defined:
            ui.errors.Error(self, 'wikify_config() is not defined.')
            yield None

        if not ui.options.skip_clean:
            yield self.Clean(ui)

        results = yield self.Test(ui)
        template_file = os.path.join(
            os.path.dirname(__file__),
            'summary',
            'pukiwiki_full.ninja')
        content = self._Summarize(results, template_file, ui)
        self._UploadWiki(content, ui)
        yield None


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
