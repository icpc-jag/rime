#!/usr/bin/python

import fnmatch
import os.path

from rime.basic import consts
import rime.basic.targets.testset  # NOQA
from rime.basic import test
from rime.core import targets
from rime.core import taskgraph
from rime.util import files


class TestMerger(object):
    def __init__(self, name, input_pattern,
                 input_separator, input_terminator,
                 output_separator, output_terminator):
        self.name = name
        self.input_pattern = input_pattern
        self.input_separator = input_separator
        self.input_terminator = input_terminator
        self.output_separator = output_separator
        self.output_terminator = output_terminator

    def Run(self, testcases, merged_testcase, ui):
        infiles = [t.infile for t in testcases
                   if fnmatch.fnmatch(os.path.basename(t.infile),
                                      self.input_pattern)]
        difffiles = [os.path.splitext(infile)[0] + consts.DIFF_EXT
                     for infile in infiles]
        ui.console.PrintAction(
            'MERGE', merged_testcase.testset,
            'Generating %s' % os.path.basename(merged_testcase.infile),
            progress=True)
        self._Concatenate(infiles, merged_testcase.infile,
                          self.input_separator,
                          self.input_terminator)
        ui.console.PrintAction(
            'MERGE', merged_testcase.testset,
            'Generating %s' % os.path.basename(merged_testcase.difffile),
            progress=True)
        self._Concatenate(difffiles, merged_testcase.difffile,
                          self.output_separator,
                          self.output_terminator)

    @classmethod
    def _Concatenate(cls, srcs, dst, separator, terminator):
        with open(dst, 'w') as f:
            for i, src in enumerate(srcs):
                if i > 0:
                    f.write(separator)
                f.write(files.ReadFile(src))
            f.write(terminator)


class MergedTestCase(test.TestCase):
    def __init__(self, testset, merger):
        super(MergedTestCase, self).__init__(
            testset,
            os.path.join(testset.out_dir, '%s%s' %
                         (merger.name, consts.IN_EXT)))
        self.merger = merger

    @property
    def timeout(self):
        return None


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.mergers = []

    def PreLoad(self, ui):
        super(Testset, self).PreLoad(ui)

        def merged_test(name=None, input_pattern=('*' + consts.IN_EXT),
                        input_separator='', input_terminator='',
                        output_separator='', output_terminator=''):
            if name is None:
                name = 'M%s' % len(self.mergers)
            merger = TestMerger(name, input_pattern,
                                input_separator, input_terminator,
                                output_separator, output_terminator)
            for name in ('input_separator', 'input_terminator',
                         'output_separator', 'output_terminator'):
                value = locals()[name]
                if value and not value.endswith('\n'):
                    ui.errors.Warning(
                        self, 'merged_test(): %s not ending with \\n.' % name)
            self.mergers.append(merger)
        self.exports['merged_test'] = merged_test

    @taskgraph.task_method
    def _PostBuildHook(self, ui):
        if not (yield super(Testset, self)._PostBuildHook(ui)):
            yield False
        yield all((yield taskgraph.TaskBranch([
            self._GenerateMergedTest(testcase, ui)
            for testcase in self.GetMergedTestCases()])))

    @taskgraph.task_method
    def _GenerateMergedTest(self, merged_testcase, ui):
        merged_testcase.merger.Run(self.ListTestCases(),
                                   merged_testcase,
                                   ui)
        yield True

    @taskgraph.task_method
    def _TestSolutionWithAllCases(self, solution, ui):
        original_result = (
            yield super(Testset, self)._TestSolutionWithAllCases(solution, ui))
        if original_result.expected and solution.IsCorrect() and self.mergers:
            merged_result = (
                yield self._TestSolutionWithMergedTests(solution, ui))
            original_result.results.update(merged_result.results)
            if not merged_result.expected:
                original_result.Finalize(
                    False, detail=merged_result.detail,
                    notable_testcase=merged_result.notable_testcase,
                    allow_override=True)
            else:
                if merged_result.IsTimingValid(ui):
                    detail = ('%s, %s' %
                              (original_result.detail,
                               ', '.join(['%s %.2fs' %
                                          (os.path.basename(t.infile),
                                           merged_result.results[t].time)
                                          for t in merged_result.testcases])))
                else:
                    detail = ('%s, %s' %
                              (original_result.detail,
                               ', '.join(['%s *.**s' %
                                          os.path.basename(t.infile)
                                          for t in merged_result.testcases])))
                original_result.Finalize(
                    True, detail=detail, allow_override=True)
        yield original_result

    @taskgraph.task_method
    def _TestSolutionWithMergedTests(self, solution, ui):
        testcases = self.GetMergedTestCases()
        result = test.TestsetResult(self, solution, testcases)
        # Try all cases.
        yield taskgraph.TaskBranch([
            self._TestSolutionWithAllCasesOne(solution, testcase, result, ui)
            for testcase in testcases],
            unsafe_interrupt=True)
        if not result.IsFinalized():
            result.Finalize(True, 'okay')
        yield result

    def ListTestCases(self):
        merged_infiles = set([t.infile for t in self.GetMergedTestCases()])
        return [t for t in super(Testset, self).ListTestCases()
                if t.infile not in merged_infiles]

    def GetMergedTestCases(self):
        return [MergedTestCase(self, merger) for merger in self.mergers]


targets.registry.Override('Testset', Testset)
