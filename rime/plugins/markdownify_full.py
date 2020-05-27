#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import os.path

import rime.basic.targets.project  # NOQA
from rime.core import commands as rime_commands  # NOQA
from rime.core import targets  # NOQA
from rime.core import taskgraph  # NOQA


class Project(targets.registry.Project):
    @taskgraph.task_method
    def MarkdownifyFull(self, ui):
        if not ui.options.skip_clean:
            yield self.Clean(ui)

        results = yield self.Test(ui)
        template_file = os.path.join(
            os.path.dirname(__file__),
            'summary',
            'md.ninja')
        content = self._Summarize(results, template_file, ui)
        out_file = os.path.join(self.base_dir, 'summary.md')
        codecs.open(out_file, 'w', 'utf8').write(content)
        yield None


class MarkdownifyFull(rime_commands.CommandBase):
    def __init__(self, parent):
        super(MarkdownifyFull, self).__init__(
            'markdownify_full',
            '',
            'Markdownify full plugin',
            '',
            parent)
        self.AddOptionEntry(rime_commands.OptionEntry(
            's', 'skip_clean', 'skip_clean', bool, False, None,
            'Skip cleaning generated files up.'
        ))

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
