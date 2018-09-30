#!/usr/bin/python

import os
import os.path

from rime.basic import consts
import rime.basic.targets.testset   # NOQA
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import commands as plus_commands
from rime.util import files


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.mjudge_pack_dir = os.path.join(self.problem.out_dir, 'mjudge')


class MJudgePacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        testcases = testset.ListTestCases()
        try:
            files.RemoveTree(testset.mjudge_pack_dir)
            files.MakeDir(testset.mjudge_pack_dir)
        except Exception:
            ui.errors.Exception(testset)
            yield False
        for (i, testcase) in enumerate(testcases):
            basename = os.path.splitext(testcase.infile)[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile = str(i + 1) + consts.IN_EXT
            packed_difffile = str(i + 1) + consts.DIFF_EXT
            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(testcase.infile),
                                  packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(testset.mjudge_pack_dir,
                                            packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(difffile), packed_difffile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, difffile),
                               os.path.join(testset.mjudge_pack_dir,
                                            packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False
        yield True


targets.registry.Override('Testset', Testset)

plus_commands.packer_registry.Add(MJudgePacker)
