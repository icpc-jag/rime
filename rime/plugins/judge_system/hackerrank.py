#!/usr/bin/python

import os
import os.path
import shutil

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
        self.hackerrank_pack_dir = os.path.join(self.problem.out_dir,
                                                'hackerrank')


class HackerRankPacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        testcases = testset.ListTestCases()
        try:
            files.RemoveTree(testset.hackerrank_pack_dir)
            files.MakeDir(testset.hackerrank_pack_dir)
            files.MakeDir(os.path.join(testset.hackerrank_pack_dir, 'input'))
            files.MakeDir(os.path.join(testset.hackerrank_pack_dir, 'output'))
        except Exception:
            ui.errors.Exception(testset)
            yield False
        for (i, testcase) in enumerate(testcases):
            basename = os.path.splitext(testcase.infile)[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile = 'input' + ('%02d' % i) + '.txt'
            packed_difffile = 'output' + ('%02d' % i) + '.txt'
            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> input/%s' % (os.path.basename(testcase.infile),
                                        packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(testset.hackerrank_pack_dir,
                                            'input',
                                            packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> output/%s' % (os.path.basename(difffile),
                                         packed_difffile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, difffile),
                               os.path.join(testset.hackerrank_pack_dir,
                                            'output',
                                            packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        # hackerrank.zip
        try:
            shutil.make_archive(
                os.path.join(testset.hackerrank_pack_dir, 'hackerrank'),
                'zip',
                os.path.join(testset.hackerrank_pack_dir))
            ui.console.PrintAction(
                'PACK', testset, 'zipped to hackerrank.zip', progress=True)
        except Exception as e:
            ui.errors.Exception(testset)
            yield False

        # case.txt
        files.WriteFile(str(len(testcases)),
                        os.path.join(testset.hackerrank_pack_dir, 'case.txt'))

        # build.sh
        # TODO(mizuno): reactive
        checker = testset.judges[0]
        if (len(testset.judges) == 1 and
                not isinstance(checker, basic_codes.InternalDiffCode)):
            ui.console.PrintAction(
                'PACK', testset, 'checker files', progress=True)
            files.CopyFile(os.path.join(testset.src_dir, checker.src_name),
                           os.path.join(testset.hackerrank_pack_dir,
                                        'checker.cpp'))
            for f in checker.dependency:
                files.CopyFile(os.path.join(testset.project.library_dir, f),
                               os.path.join(testset.hackerrank_pack_dir, f))
            files.WriteFile(
                '#!/bin/bash\ng++ -o checker -std=c++11 checker.cpp',
                os.path.join(testset.hackerrank_pack_dir, 'build.sh'))
        elif len(testset.judges) > 1:
            ui.errors.Error(
                testset, "Multiple output checker is not supported!")
            yield False

        # HACKERRANKCONF
        hackerrank_conf = '''\
# -*- coding: utf-8; mode: python -*-

# Problem ID
PROBLEM_ID = '*'

# Judge type
#   'diff-validator' for a problem without special judge
#   'float-validator' for a problem with floating point validator
#   'special-validator' for a problem with special validator
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
                hackerrank_conf.format(
                    'JUDGE_TYPE = \'special-validator\'',
                    testset.problem.title),
                os.path.join(testset.hackerrank_pack_dir, 'HACKERRANKCONF'))
        else:
            files.WriteFile(
                hackerrank_conf.format(
                    'JUDGE_TYPE = \'diff-validator\'', testset.problem.title),
                os.path.join(testset.hackerrank_pack_dir, 'HACKERRANKCONF'))

        yield True


targets.registry.Override('Testset', Testset)

plus_commands.packer_registry.Add(HackerRankPacker)
