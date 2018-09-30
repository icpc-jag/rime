#!/usr/bin/python

import fnmatch
import os.path

from rime.basic import consts
import rime.basic.targets.testset  # NOQA
from rime.basic import test
from rime.core import targets
from rime.core import taskgraph
from rime.util import class_registry
from rime.util import files

consts.IN_ORIGINAL_EXT = '.in_orig'


class TestMerger(object):
    def __init__(self, output_replace=None):
        self.output_replace = output_replace

    def Run(self, testcases, merged_testcase, ui):
        infiles = [os.path.splitext(t.infile)[0] + consts.IN_ORIGINAL_EXT
                   for t in testcases]
        difffiles = [os.path.splitext(infile)[0] + consts.DIFF_EXT
                     for infile in infiles]
        ui.console.PrintAction(
            'MERGE', merged_testcase.testset,
            'Generating %s' % os.path.basename(merged_testcase.infile),
            progress=True)
        self._ConcatenateIn(infiles, merged_testcase.infile)
        ui.console.PrintAction(
            'MERGE', merged_testcase.testset,
            'Generating %s' % os.path.basename(merged_testcase.difffile),
            progress=True)
        self._ConcatenateDiff(difffiles, merged_testcase.difffile)

    def _ConcatenateIn(self, srcs, dst):
        raise NotImplementedError()

    def _ConcatenateDiff(self, srcs, dst):
        # avoid overwriting
        if any([os.path.exists(src) and src != dst for src in srcs]):
            with open(dst, 'w') as f:
                for i, src in enumerate(srcs):
                    if self.output_replace:
                        f.write(self.output_replace(
                            i + 1, files.ReadFile(src)))
                    else:
                        f.write(files.ReadFile(src))


class ICPCMerger(TestMerger):
    PREFIX = 'icpc'

    def __init__(self, input_terminator, output_replace=None):
        super(ICPCMerger, self).__init__(output_replace)
        self.input_terminator = input_terminator
        if self.input_terminator and not self.input_terminator.endswith('\n'):
            raise RuntimeError(
                'icpc_merger(): input_terminator is not ending with \\n.')

    def _ConcatenateIn(self, srcs, dst):
        with open(dst, 'w') as f:
            for i, src in enumerate(srcs):
                f.write(files.ReadFile(src))
            f.write(self.input_terminator)


class GCJMerger(TestMerger):
    PREFIX = 'gcj'

    def __init__(self, output_replace=None):
        super(GCJMerger, self).__init__(output_replace)

    def _ConcatenateIn(self, srcs, dst):
        with open(dst, 'w') as f:
            f.write(str(len(srcs)) + '\n')
            for i, src in enumerate(srcs):
                f.write(files.ReadFile(src))


test_merger_registry = class_registry.ClassRegistry(TestMerger)
test_merger_registry.Add(ICPCMerger)
test_merger_registry.Add(GCJMerger)


class MergedTestCase(test.TestCase):
    def __init__(self, testset, name, input_pattern):
        super(MergedTestCase, self).__init__(
            testset,
            os.path.join(testset.out_dir,
                         '{0}{1}'.format(name, consts.IN_EXT)))
        self.input_pattern = input_pattern

    @property
    def timeout(self):
        return None


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.test_merger = None
        self.merged_testcases = []

    def PreLoad(self, ui):
        super(Testset, self).PreLoad(ui)

        for test_merger in test_merger_registry.classes.values():
            # to make a new environment
            def Closure(test_merger):
                def Registerer(*args, **kwargs):
                    if self.test_merger:
                        raise RuntimeError('Multiple test merger registered.')
                    self.test_merger = test_merger(*args, **kwargs)
                self.exports['{0}_merger'.format(
                    test_merger.PREFIX)] = Registerer
            Closure(test_merger)

        def casenum_replace(case_pattern, case_replace):
            return lambda i, src: src.replace(
                case_pattern, case_replace.format(i))
        self.exports['casenum_replace'] = casenum_replace

        def merged_testset(name, input_pattern):
            self.merged_testcases.append(
                MergedTestCase(self, name, input_pattern))
        self.exports['merged_testset'] = merged_testset

    @taskgraph.task_method
    def _RunGenerators(self, ui):
        if not (yield super(Testset, self)._RunGenerators(ui)):
            yield False

        # convert to merged case
        if self.test_merger:
            for testcase in self.ListTestCases():
                src = testcase.infile
                dst = os.path.splitext(src)[0] + consts.IN_ORIGINAL_EXT
                files.CopyFile(src, dst)
                self.test_merger.Run([testcase], testcase, ui)

        yield True

    @taskgraph.task_method
    def _PostBuildHook(self, ui):
        if not (yield super(Testset, self)._PostBuildHook(ui)):
            yield False
        if not all((yield taskgraph.TaskBranch([
                self._GenerateMergedTest(testcase, ui)
                for testcase in self.GetMergedTestCases()]))):
            yield False

        if not all((yield taskgraph.TaskBranch([
                self._ValidateMergedTest(testcase, ui)
                for testcase in self.GetMergedTestCases()]))):
            yield False

        yield True

    @taskgraph.task_method
    def _GenerateMergedTest(self, merged_testcase, ui):
        if not self.test_merger:
            ui.errors.Error(self, "No merger registered!")
            yield False

        testcases = [t for t in self.ListTestCases()
                     if fnmatch.fnmatch(os.path.basename(t.infile),
                                        merged_testcase.input_pattern)]
        self.test_merger.Run(testcases, merged_testcase, ui)
        yield True

    @taskgraph.task_method
    def _ValidateMergedTest(self, merged_testcase, ui):
        if not self.validators:
            if self.base_dir:
                ui.errors.Warning(self, 'Validator unavailable')
            yield True
        testcases = self.GetMergedTestCases()
        results = yield taskgraph.TaskBranch([
            self._RunValidatorOne(validator, testcase, ui)
            for validator in self.validators
            for testcase in testcases])
        if not all(results):
            yield False
        ui.console.PrintAction('VALIDATE', self, 'OK Merged Cases')
        yield True

    @taskgraph.task_method
    def _TestSolutionWithAllCases(self, solution, ui):
        original_result = (
            yield super(Testset, self)._TestSolutionWithAllCases(solution, ui))
        if (original_result.expected and
                solution.IsCorrect() and
                self.merged_testcases):
            merged_result = (yield self._TestSolutionWithMergedTests(
                solution, ui))
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
        return self.merged_testcases


targets.registry.Override('Testset', Testset)
