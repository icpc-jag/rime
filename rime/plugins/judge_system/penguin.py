#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path

from rime.basic import consts
import rime.basic.targets.problem
import rime.basic.targets.project
import rime.basic.targets.solution
import rime.basic.targets.testset  # NOQA
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import commands as plus_commands
from rime.util import files


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.penguin_pack_dir = os.path.join(self.problem.out_dir, 'penguin')


class PenguinPacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        testcases = testset.ListTestCases()
        try:
            files.RemoveTree(testset.penguin_pack_dir)
            files.MakeDir(testset.penguin_pack_dir)
            files.MakeDir(os.path.join(testset.penguin_pack_dir, 'input'))
            files.MakeDir(os.path.join(testset.penguin_pack_dir, 'output'))
            files.CopyFile(os.path.join(testset.problem.base_dir, 'README.md'),
                           os.path.join(testset.penguin_pack_dir, 'README.md'))
        except Exception:
            ui.errors.Exception(testset)
            yield False

        for testcase in testcases:
            basename = os.path.splitext(testcase.infile)[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile =\
                os.path.join('input', os.path.basename(basename) + '.in')
            packed_difffile =\
                os.path.join('output', os.path.basename(basename) + '.out')
            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(testcase.infile),
                                  packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(testset.penguin_pack_dir,
                                            packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(difffile), packed_difffile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, difffile),
                               os.path.join(testset.penguin_pack_dir,
                                            packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        yield True


targets.registry.Override('Testset', Testset)

plus_commands.packer_registry.Add(PenguinPacker)
