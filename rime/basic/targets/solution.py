#!/usr/bin/python

import itertools

from rime.basic.targets import problem
from rime.core import codes
from rime.core import targets
from rime.core import taskgraph
from rime.util import files


class Solution(targets.TargetBase, problem.ProblemComponentMixin):
    """Solution target."""

    CONFIG_FILENAME = 'SOLUTION'

    def __init__(self, name, base_dir, parent):
        assert isinstance(parent, problem.Problem)
        super(Solution, self).__init__(name, base_dir, parent)
        self.project = parent.project
        self.problem = parent
        problem.ProblemComponentMixin.__init__(self)

    def PreLoad(self, ui):
        super(Solution, self).PreLoad(ui)
        self._codes = []
        self.exports.update(
            codes.CreateDictionary('%s_solution',
                                   self._codes,
                                   src_dir=self.src_dir,
                                   out_dir=self.out_dir,
                                   wrapper=self._WrapSolution))

    def _WrapSolution(self, code_class):
        def Wrapped(src_name, src_dir, out_dir, challenge_cases=None,
                    *args, **kwargs):
            code = code_class(src_name, src_dir, out_dir, *args, **kwargs)
            self.challenge_cases = challenge_cases
            return code
        return Wrapped

    def PostLoad(self, ui):
        super(Solution, self).PostLoad(ui)
        if len(self._codes) == 0:
            self._CompatGuessSolution(ui)
        if len(self._codes) >= 2:
            raise targets.ConfigurationError('multiple solutions')
        if len(self._codes) == 0:
            raise targets.ConfigurationError('no solution definition found')
        self.code = self._codes[0]

    def _CompatGuessSolution(self, ui):
        wrapped_auto_code = self._WrapSolution(codes.AutoCode)
        for filename in files.ListDir(self.src_dir):
            try:
                code = wrapped_auto_code(filename, self.src_dir, self.out_dir)
                self._codes.append(code)
            except codes.UnknownCodeExtensionException:
                continue

    def IsCorrect(self):
        """Returns whether this is correct solution."""
        return self.challenge_cases is None

    @taskgraph.task_method
    def Build(self, ui):
        """Build this solution."""
        if self.IsBuildCached():
            ui.console.PrintAction(
                'COMPILE', self, 'up-to-date', progress=True)
            yield True
        files.MakeDir(self.out_dir)
        if not self.code.QUIET_COMPILE:
            ui.console.PrintAction('COMPILE', self)
        res = yield self.code.Compile()
        log = self.code.ReadCompileLog()
        if res.status != codes.RunResult.OK:
            ui.errors.Error(self, 'Compile Error (%s)' % res.status)
            ui.console.PrintLog(log)
            yield False
        if log:
            ui.console.Print('Compiler warnings found:')
            ui.console.PrintLog(log)
        if not self.SetCacheStamp(ui):
            yield False
        yield True

    @taskgraph.task_method
    def Run(self, args, cwd, input, output, timeout, precise):
        """Run this solution."""
        yield (yield self.code.Run(
            args=args, cwd=cwd, input=input, output=output,
            timeout=timeout, precise=precise))

    @taskgraph.task_method
    def Test(self, ui):
        """Run tests for the solution."""
        results = yield taskgraph.TaskBranch(
            [testset.TestSolution(self, ui) for testset in
             self.problem.testsets])
        yield list(itertools.chain(*results))

    @taskgraph.task_method
    def Clean(self, ui):
        """Clean the solution."""
        ui.console.PrintAction('CLEAN', self)
        e = yield self.code.Clean()
        if e:
            ui.errors.Exception(self, e)
            yield False
        yield True


targets.registry.Add(Solution)
