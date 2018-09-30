#!/usr/bin/python

import os.path

from rime.basic import consts
import rime.basic.targets.testset  # NOQA
from rime.basic import test
from rime.core import codes as core_codes
from rime.core import targets
from rime.core import taskgraph
from rime.util import class_registry


class JudgeRunner(object):
    def Run(self, infile, difffile, outfile, cwd, judgefile):
        raise NotImplementedError()


class RimeJudgeRunner(JudgeRunner):
    PREFIX = 'rime'

    def Run(self, judge, infile, difffile, outfile, cwd, judgefile):
        return judge.Run(
            args=('--infile', infile,
                  '--difffile', difffile,
                  '--outfile', outfile),
            cwd=cwd,
            input=os.devnull,
            output=judgefile,
            timeout=None, precise=False,
            redirect_error=True)  # !redirect_error


class TestlibJudgeRunner(JudgeRunner):
    PREFIX = 'testlib'

    def Run(self, judge, infile, difffile, outfile, cwd, judgefile):
        return judge.Run(
            args=(infile, outfile, difffile),
            cwd=cwd,
            input=os.devnull,
            output=judgefile,
            timeout=None, precise=False,
            redirect_error=True)  # !redirect_error


judge_runner_registry = class_registry.ClassRegistry(JudgeRunner)
judge_runner_registry.Add(RimeJudgeRunner)
judge_runner_registry.Add(TestlibJudgeRunner)


class ReactiveRunner(object):
    def Run(self, reactive, solution, args, cwd, input, output, timeout,
            precise):
        raise NotImplementedError()


class KUPCReactiveRunner(ReactiveRunner):
    PREFIX = 'kupc'

    def Run(self, reactive, args, cwd, input, output, timeout, precise):
        return reactive.Run(
            args=("'%s'" % ' '.join(args),),
            cwd=cwd,
            input=input,
            output=output,
            timeout=timeout,
            precise=precise,
            redirect_error=True)  # !redirect_error


class TestlibReactiveRunner(ReactiveRunner):
    PREFIX = 'testlib'

    def Run(self, reactive, solution, args, cwd, input, output, timeout,
            precise):
        raise NotImplementedError()


class NEERCReactiveRunner(ReactiveRunner):
    PREFIX = 'neerc'

    def Run(self, reactive, solution, args, cwd, input, output, timeout,
            precise):
        raise NotImplementedError()


reactive_runner_registry = class_registry.ClassRegistry(ReactiveRunner)
reactive_runner_registry.Add(KUPCReactiveRunner)
# reactive_runner_registry.Add(TestlibReactiveRunner)
# reactive_runner_registry.Add(NEERCReactiveRunner)


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)

        for judge_runner in judge_runner_registry.classes.values():
            self.exports['{0}_judge_runner'.format(
                judge_runner.PREFIX)] = judge_runner()

        for reactive_runner in reactive_runner_registry.classes.values():
            self.exports['{0}_reactive_runner'.format(
                reactive_runner.PREFIX)] = reactive_runner()

    @taskgraph.task_method
    def _TestOneCaseNoCache(self, solution, testcase, ui):
        """Test a solution with one case.

        Never cache results.
        Returns TestCaseResult.
        """
        outfile, judgefile = [
            os.path.join(
                solution.out_dir,
                os.path.splitext(os.path.basename(testcase.infile))[0] + ext)
            for ext in (consts.OUT_EXT, consts.JUDGE_EXT)]
        precise = (ui.options.precise or ui.options.parallelism <= 1)
        # reactive
        if self.reactives:
            if len(self.reactives) > 1:
                ui.errors.Error(self, "Multiple reactive checkers registered.")
                yield None
            reactive = self.reactives[0]
            if not reactive.variant:
                reactive.variant = KUPCReactiveRunner()
            res = yield reactive.variant.Run(
                reactive=reactive,
                args=solution.code.run_args, cwd=solution.out_dir,
                input=testcase.infile,
                output=outfile,
                timeout=testcase.timeout, precise=precise)
        else:
            res = yield solution.Run(
                args=(), cwd=solution.out_dir,
                input=testcase.infile,
                output=outfile,
                timeout=testcase.timeout, precise=precise)
        if res.status == core_codes.RunResult.TLE:
            yield test.TestCaseResult(solution, testcase,
                                      test.TestCaseResult.TLE,
                                      time=None, cached=False)
        if res.status != core_codes.RunResult.OK:
            yield test.TestCaseResult(solution, testcase,
                                      test.TestCaseResult.RE,
                                      time=None, cached=False)

        time = res.time
        for judge in self.judges:
            if not judge.variant:
                judge.variant = RimeJudgeRunner()
            res = yield judge.variant.Run(
                judge=judge,
                infile=testcase.infile,
                difffile=testcase.difffile,
                outfile=outfile,
                cwd=self.out_dir,
                judgefile=judgefile)
            if res.status == core_codes.RunResult.NG:
                yield test.TestCaseResult(solution, testcase,
                                          test.TestCaseResult.WA,
                                          time=None, cached=False)
            elif res.status != core_codes.RunResult.OK:
                yield test.TestCaseResult(
                    solution, testcase,
                    test.TestVerdict('Validator %s' % res.status),
                    time=None, cached=False)
        yield test.TestCaseResult(solution, testcase, test.TestCaseResult.AC,
                                  time=time, cached=False)

    @taskgraph.task_method
    def _RunReferenceSolutionOne(self, reference_solution, testcase, ui):
        """Run the reference solution against a single input file."""
        if os.path.isfile(testcase.difffile):
            yield True
        # reactive
        if self.reactives:
            if len(self.reactives) > 1:
                ui.errors.Error(self, "Multiple reactive checkers registered.")
                yield None
            reactive = self.reactives[0]
            if not reactive.variant:
                reactive.variant = KUPCReactiveRunner()
            res = yield reactive.variant.Run(
                reactive=reactive,
                args=reference_solution.code.run_args,
                cwd=reference_solution.out_dir,
                input=testcase.infile,
                output=testcase.difffile,
                timeout=None, precise=False)
        else:
            res = yield reference_solution.Run(
                args=(), cwd=reference_solution.out_dir,
                input=testcase.infile,
                output=testcase.difffile,
                timeout=None, precise=False)
        if res.status != core_codes.RunResult.OK:
            ui.errors.Error(reference_solution, res.status)
            raise taskgraph.Bailout([False])
        ui.console.PrintAction('REFRUN', reference_solution,
                               '%s: DONE' % os.path.basename(testcase.infile),
                               progress=True)
        yield True

    @taskgraph.task_method
    def _CompileJudges(self, ui):
        res = (yield super(Testset, self)._CompileJudges(ui))
        if not res:
            yield False

        results = yield taskgraph.TaskBranch([
            self._CompileReactiveOne(reactive, ui)
            for reactive in self.reactives])
        yield all(results)

    @taskgraph.task_method
    def _CompileReactiveOne(self, reactive, ui):
        """Compile a single reative."""
        if not reactive.QUIET_COMPILE:
            ui.console.PrintAction('COMPILE', self, reactive.src_name)
        res = yield reactive.Compile()
        if res.status != core_codes.RunResult.OK:
            ui.errors.Error(self, '%s: Compile Error (%s)'
                            % (reactive.src_name, res.status))
            ui.console.PrintLog(reactive.ReadCompileLog())
            yield False
        yield True


targets.registry.Override('Testset', Testset)
