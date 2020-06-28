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
    def HtmlifyFull(self, ui):
        if not ui.options.skip_clean:
            yield self.Clean(ui)

        results = yield self.Test(ui)
        template_file = os.path.join(
            os.path.dirname(__file__),
            'summary',
            'html.ninja')
        content = self._Summarize(results, template_file, ui)
        out_file = os.path.join(self.base_dir, 'summary.html')
        codecs.open(out_file, 'w', 'utf8').write(content)
        yield None


class HtmlifyFull(rime_commands.CommandBase):
    def __init__(self, parent):
        super(HtmlifyFull, self).__init__(
            'htmlify_full',
            '',
            'Htmlify full plugin',
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
