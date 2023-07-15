#!/usr/bin/python

import os
import os.path
import shutil

from rime.basic import consts
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import commands as plus_commands
from rime.util import files


class Problem(targets.registry.Problem):
    def PreLoad(self, ui):
        super(Problem, self).PreLoad(ui)
        self.domjudge_config_defined = False

        def _domjudge_config(problem_file=None, color=None):
            self.domjudge_config_defined = True
            self.domjudge_problem_file = problem_file
            self.domjudge_color = color
        self.exports['domjudge_config'] = _domjudge_config


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.domjudge_pack_dir = os.path.join(self.problem.out_dir, 'domjudge')


class DOMJudgePacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        pack_files_dir = os.path.join(testset.domjudge_pack_dir, 'files')
        try:
            files.RemoveTree(testset.domjudge_pack_dir)
            files.MakeDir(os.path.join(pack_files_dir, 'data', 'sample'))
            files.MakeDir(os.path.join(pack_files_dir, 'data', 'secret'))

            # Generate domjudge-problem.ini
            yaml_file = os.path.join(pack_files_dir, 'domjudge-problem.ini')
            with open(yaml_file, 'w') as f:
                f.write(f'externalid = "{testset.problem.name}"\n')
                f.write(f'short-name = "{testset.problem.id}"\n')
                f.write(f'name = "{testset.problem.title}"\n')
                f.write(f'timelimit = {testset.problem.timeout}\n')
                if (testset.problem.domjudge_config_defined and
                        testset.problem.domjudge_color):
                    f.write(f'color = {testset.problem.domjudge_color}\n')
        except Exception:
            ui.errors.Exception(testset)
            yield False

        testcases = testset.ListTestCases()
        for (i, testcase) in enumerate(testcases):
            basename = os.path.splitext(os.path.basename(testcase.infile))[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile = basename + ".in"
            packed_difffile = basename + ".ans"
            is_sample = 'sample' in packed_infile
            target_dir = os.path.join(
                pack_files_dir, 'data',
                'sample' if is_sample else 'secret')

            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(testcase.infile),
                                  packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(target_dir, packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(difffile), packed_difffile),
                    progress=True)
                files.CopyFile(
                    os.path.join(testset.out_dir, testcase.difffile),
                    os.path.join(target_dir, packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        if (testset.problem.domjudge_config_defined and
                testset.problem.domjudge_problem_file):
            dest_filename = 'problem.pdf'
            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (testset.problem.domjudge_problem_file,
                                  dest_filename),
                    progress=True)
                files.CopyFile(
                    os.path.join(testset.problem.base_dir,
                                 testset.problem.domjudge_problem_file),
                    os.path.join(pack_files_dir, dest_filename))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        # Create a zip file
        try:
            shutil.make_archive(
                os.path.join(testset.domjudge_pack_dir, testset.problem.id),
                'zip',
                root_dir=pack_files_dir)
        except Exception:
            ui.errors.Exception(testset)
            yield False

        ui.console.PrintAction(
            'PACK', testset, f'Created {testset.problem.id}.zip')

        yield True


targets.registry.Override('Problem', Problem)
targets.registry.Override('Testset', Testset)

plus_commands.packer_registry.Add(DOMJudgePacker)
