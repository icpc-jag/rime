#!/usr/bin/python

import fnmatch
import os.path
import re

from rime.basic import consts
import rime.basic.targets.solution  # NOQA
import rime.basic.targets.testset  # NOQA
from rime.basic import test
from rime.core import targets
from rime.core import taskgraph
from rime.util import files


class SubtaskTestCase(test.TestCase):
    def __init__(self, testset, name, score, input_patterns):
        super(SubtaskTestCase, self).__init__(
            testset,
            name, name)
        self.name = name
        self.score = score
        self.input_patterns = input_patterns

    @property
    def timeout(self):
        return None


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.subtask_testcases = []
        self.scoring_judge = False

    def PreLoad(self, ui):
        super(Testset, self).PreLoad(ui)

        def subtask_testset(name, score=100, input_patterns=['*']):
            self.subtask_testcases.append(SubtaskTestCase(
                self, name, score, input_patterns))
        self.exports['subtask_testset'] = subtask_testset

        def scoring_judge():
            self.scoring_judge = True
        self.exports['scoring_judge'] = scoring_judge

    @taskgraph.task_method
    def _TestSolutionWithAllCases(self, solution, ui):
        original_result = (
            yield super(Testset, self)._TestSolutionWithAllCases(solution, ui))

        if self.subtask_testcases:
            max_score = 0
            min_score = 0

            for subtask in self.subtask_testcases:
                subtask_results = [
                    r for (t, r) in original_result.results.items()
                    if any([fnmatch.fnmatch(os.path.basename(t.infile),
                                            input_pattern)
                            for input_pattern in subtask.input_patterns])]
                accepted = all([result.verdict == test.TestCaseResult.AC
                                for result in subtask_results
                                if result.verdict != test.TestCaseResult.NA])
                unknown = any([result.verdict == test.TestCaseResult.NA
                               for result in subtask_results])
                if accepted:
                    if not unknown:
                        min_score += subtask.score
                    max_score += subtask.score

            if min_score == max_score:
                detail = ('%s, score %s' % (original_result.detail, min_score))
            else:
                detail = ('%s, score %s <= x <= %s' %
                          (original_result.detail, min_score, max_score))
                ui.errors.Warning(
                    self,
                    "If you want more precise score, set keep_going option.")

            if solution.expected_score is not None:
                expected_result = (min_score <= solution.expected_score and
                                   solution.expected_score <= max_score)
                if expected_result:
                    original_result.Finalize(
                        True, detail=detail, allow_override=True)
                else:
                    original_result.Finalize(
                        False,
                        notable_testcase=test.TestCase(
                            self, 'unexpected_score.in'),
                        detail=detail, allow_override=True)
                    if min_score == max_score:
                        ui.errors.Error(self,
                                        'expected score %s does not equal to '
                                        '%s' %
                                        (solution.expected_score, min_score))
                    else:
                        ui.errors.Error(
                            self,
                            'expected score x = %s does not satisfy'
                            '%s <= x <= %s' %
                            (solution.expected_score, min_score, max_score))
            elif original_result.expected:
                original_result.Finalize(
                    True, detail=detail, allow_override=True)
            else:
                original_result.Finalize(
                    False,
                    notable_testcase=original_result.notable_testcase,
                    detail=detail, allow_override=True)

        elif original_result.IsAccepted() and self.scoring_judge:
            score = 0
            p = re.compile("IMOJUDGE<<<(\\d+)>>>")
            for (testcase, result) in original_result.results.items():
                judge_detail = files.ReadFile(
                    os.path.join(
                        solution.out_dir,
                        os.path.splitext(
                            os.path.basename(testcase.infile))[0] +
                        consts.JUDGE_EXT))
                if judge_detail:
                    judge_detail = judge_detail.strip()
                    if judge_detail.isdigit():
                        score += int(judge_detail)
                    elif p.search(judge_detail):
                        score += int(p.search(judge_detail).group(1))
                    else:
                        ui.errors.Error(
                            self,
                            'the judge result does not indicate a score:'
                            '"%s"' % (judge_detail))
                        original_result.Finalize(
                            False,
                            notable_testcase=test.TestCase(
                                self, 'judge_error.in'),
                            detail=original_result.detail, allow_override=True)
                        yield original_result
                else:
                    ui.errors.Error(self, 'the judge is silent.')
                    original_result.Finalize(
                        False,
                        notable_testcase=test.TestCase(self, 'judge_error.in'),
                        detail=original_result.detail, allow_override=True)
                    yield original_result
            score /= float(len(original_result.results))
            detail = ('%s, score %s' %
                      (original_result.detail, score))
            expected_result = score == solution.expected_score
            if expected_result or not solution.expected_score:
                original_result.Finalize(
                    True, detail=detail, allow_override=True)
            else:
                original_result.Finalize(
                    False,
                    notable_testcase=test.TestCase(
                        self, 'unexpected_score.in'),
                    detail=detail, allow_override=True)
                ui.errors.Error(self,
                                'expected score %d does not equal to %s' %
                                (solution.expected_score, score))
            original_result.Finalize(True, detail=detail, allow_override=True)
        yield original_result


class Solution(targets.registry.Solution):
    def __init__(self, *args, **kwargs):
        super(Solution, self).__init__(*args, **kwargs)
        self.expected_score = None

    def PreLoad(self, ui):
        super(Solution, self).PreLoad(ui)

        def expected_score(score):
            self.expected_score = score
        self.exports['expected_score'] = expected_score


targets.registry.Override('Solution', Solution)
targets.registry.Override('Testset', Testset)
