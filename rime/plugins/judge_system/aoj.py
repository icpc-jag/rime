#!/usr/bin/python

import os
import os.path

from rime.basic import codes as basic_codes
from rime.basic import consts
import rime.basic.targets.testset   # NOQA
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import commands as plus_commands
from rime.util import files


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.aoj_pack_dir = os.path.join(self.problem.out_dir, 'aoj')


class AOJPacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        testcases = testset.ListTestCases()
        try:
            files.RemoveTree(testset.aoj_pack_dir)
            files.MakeDir(testset.aoj_pack_dir)
        except Exception:
            ui.errors.Exception(testset)
            yield False
        for (i, testcase) in enumerate(testcases):
            basename = os.path.splitext(testcase.infile)[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile = 'in' + str(i + 1) + '.txt'
            packed_difffile = 'out' + str(i + 1) + '.txt'
            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(testcase.infile),
                                  packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(testset.aoj_pack_dir,
                                            packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(difffile), packed_difffile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, difffile),
                               os.path.join(testset.aoj_pack_dir,
                                            packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        # case.txt
        files.WriteFile(str(len(testcases)),
                        os.path.join(testset.aoj_pack_dir, 'case.txt'))

        # build.sh
        # TODO(mizuno): reactive
        checker = testset.judges[0]
        if (len(testset.judges) == 1 and
                not isinstance(checker, basic_codes.InternalDiffCode)):
            ui.console.PrintAction(
                'PACK', testset, 'checker files', progress=True)
            files.CopyFile(os.path.join(testset.src_dir, checker.src_name),
                           os.path.join(testset.aoj_pack_dir, 'checker.cpp'))
            for f in checker.dependency:
                files.CopyFile(os.path.join(testset.project.library_dir, f),
                               os.path.join(testset.aoj_pack_dir, f))
            files.WriteFile(
                '#!/bin/bash\ng++ -o checker -std=c++11 checker.cpp',
                os.path.join(testset.aoj_pack_dir, 'build.sh'))
        elif len(testset.judges) > 1:
            ui.errors.Error(
                testset, "Multiple output checker is not supported!")
            yield False

        # AOJCONF
        aoj_conf = '''\
# -*- coding: utf-8; mode: python -*-

# Problem ID
PROBLEM_ID = '*'

# Judge type
#   'diff-validator' for a problem without special judge
#   'float-validator' for a problem with floating point validator
#   'special-validator' for a problem with special validator
#   'reactive' for a reactive problem
{0}

# Language of problem description
#   'ja', 'en' or 'ja-en'
DOCUMENT_TYPE = '*'

# Title of the problem
TITLE = '{1}'

# Time limit (integer, in seconds)
TIME_LIMIT = 1

# Memory limit (integer, in KB)
MEMORY_LIMIT = 32768

# Date when the problem description will be able to be seen
PUBLICATION_DATE = datetime.datetime(*, *, *, *, *)
'''
        if not isinstance(checker, basic_codes.InternalDiffCode):
            files.WriteFile(
                aoj_conf.format(
                    'JUDGE_TYPE = \'special-validator\'',
                    testset.problem.title),
                os.path.join(testset.aoj_pack_dir, 'AOJCONF'))
        else:
            files.WriteFile(
                aoj_conf.format(
                    'JUDGE_TYPE = \'diff-validator\'', testset.problem.title),
                os.path.join(testset.aoj_pack_dir, 'AOJCONF'))

        yield True


targets.registry.Override('Testset', Testset)

plus_commands.packer_registry.Add(AOJPacker)
