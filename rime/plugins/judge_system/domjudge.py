#!/usr/bin/python

import os
import os.path
import shutil

from rime.basic import consts
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import commands as plus_commands
from rime.util import files


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.domjudge_pack_dir = os.path.join(self.problem.out_dir, 'domjudge')


class DOMJudgePacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        testcases = testset.ListTestCases()
        try:
            files.RemoveTree(testset.domjudge_pack_dir)
            files.MakeDir(testset.domjudge_pack_dir)
            files.MakeDir(os.path.join(testset.domjudge_pack_dir, 'data'))
            files.MakeDir(os.path.join(testset.domjudge_pack_dir, 'data',
                                       'sample'))
            files.MakeDir(os.path.join(testset.domjudge_pack_dir, 'data',
                                       'secret'))

            # Generate problem.yaml
            yaml_file = os.path.join(testset.domjudge_pack_dir, 'problem.yaml')
            with open(yaml_file, 'w') as f:
                f.write('name: {}\n'.format(testset.problem.name))
        except Exception:
            ui.errors.Exception(testset)
            yield False
        for (i, testcase) in enumerate(testcases):
            basename = os.path.splitext(os.path.basename(testcase.infile))[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile = basename + ".in"
            packed_difffile = basename + ".ans"
            is_sample = 'sample' in packed_infile
            packed_files_dir = os.path.join(
                testset.domjudge_pack_dir, 'data',
                'sample' if is_sample else 'secret')

            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(testcase.infile),
                                  packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(packed_files_dir, packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(difffile), packed_difffile),
                    progress=True)
                files.CopyFile(
                    os.path.join(testset.out_dir, testcase.difffile),
                    os.path.join(packed_files_dir, packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        # Create a zip file
        # TODO(chiro): Add problem.pdf
        try:
            shutil.make_archive(
                os.path.join(testset.domjudge_pack_dir, testset.problem.id),
                'zip',
                root_dir=testset.domjudge_pack_dir)
        except Exception:
            ui.errors.Exception(testset)
            yield False

        yield True


targets.registry.Override('Testset', Testset)

plus_commands.packer_registry.Add(DOMJudgePacker)
