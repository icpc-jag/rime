#!/usr/bin/python

import itertools
import os.path

from rime.basic import consts
from rime.basic.targets import project
from rime.core import targets
from rime.core import taskgraph
from rime.util import files


class Problem(targets.TargetBase):
    """Problem target."""

    CONFIG_FILENAME = 'PROBLEM'

    def __init__(self, name, base_dir, parent):
        assert isinstance(parent, project.Project)
        super(Problem, self).__init__(name, base_dir, parent)
        self.project = parent
        self.problem = self
        self.out_dir = os.path.join(self.problem.base_dir, consts.RIME_OUT_DIR)

    def PreLoad(self, ui):
        super(Problem, self).PreLoad(ui)
        self.problem_defined = False

        def _problem(time_limit, reference_solution=None,
                     title=None, id=None, **kwargs):
            assert not self.problem_defined, 'Multiple problem definitions'
            self.problem_defined = True
            self.timeout = time_limit
            self.reference_solution = reference_solution
            self.title = title or self.name
            self.id = id
            for key in kwargs:
                ui.errors.Warning(
                    self, 'Unknown parameter for problem(): %s' % key)
        self.exports['problem'] = _problem

    def PostLoad(self, ui):
        super(Problem, self).PostLoad(ui)
        assert self.problem_defined, 'No problem definition found'
        self._ChainLoad(ui)
        self._ParseSettings(ui)

    def _ChainLoad(self, ui):
        # Chain-load solutions.
        self.solutions = []
        for name in sorted(files.ListDir(self.base_dir)):
            path = os.path.join(self.base_dir, name)
            if targets.registry.Solution.CanLoadFrom(path):
                solution = targets.registry.Solution(name, path, self)
                try:
                    solution.Load(ui)
                    self.solutions.append(solution)
                except targets.ConfigurationError:
                    ui.errors.Exception(solution)
        # Chain-load testsets.
        self.testsets = []
        for name in sorted(files.ListDir(self.base_dir)):
            path = os.path.join(self.base_dir, name)
            if targets.registry.Testset.CanLoadFrom(path):
                testset = targets.registry.Testset(name, path, self)
                try:
                    testset.Load(ui)
                    self.testsets.append(testset)
                except targets.ConfigurationError:
                    ui.errors.Exception(testset)

    def _ParseSettings(self, ui):
        # Currently we only support one testset per problem.
        self.testset = None
        if len(self.testsets) >= 2:
            ui.errors.Error(self, 'Multiple testsets found')
        elif len(self.testsets) == 0:
            self.testset = targets.registry.Testset.CreateEmpty(self, ui)
        elif len(self.testsets) == 1:
            self.testset = self.testsets[0]

        if self.timeout is None:
            ui.errors.Error(self, 'Time limit is not specified')

        # Select a reference solution.
        if self.reference_solution is None:
            # If not explicitly specified, select one which is
            # not marked as incorrect.
            for solution in self.solutions:
                if solution.IsCorrect():
                    self.reference_solution = solution
                    break

        else:
            # If explicitly specified, just use it.
            reference_solution_name = self.reference_solution
            self.reference_solution = None
            for solution in self.solutions:
                if solution.name == reference_solution_name:
                    self.reference_solution = solution
                    break
            if self.reference_solution is None:
                ui.errors.Error(
                    self,
                    ('Reference solution "%s" does not exist' %
                     reference_solution_name))

    def FindByBaseDir(self, base_dir):
        if self.base_dir == base_dir:
            return self
        for solution in self.solutions:
            obj = solution.FindByBaseDir(base_dir)
            if obj:
                return obj
        for testset in self.testsets:
            obj = testset.FindByBaseDir(base_dir)
            if obj:
                return obj
        return None

    @taskgraph.task_method
    def Build(self, ui):
        """Build all solutions and the testset."""
        results = yield taskgraph.TaskBranch(
            [solution.Build(ui) for solution in self.solutions] +
            [self.testset.Build(ui)])
        yield all(results)

    @taskgraph.task_method
    def Test(self, ui):
        """Run tests in the problem."""
        results = yield taskgraph.TaskBranch(
            [testset.Test(ui) for testset in self.testsets])
        yield list(itertools.chain(*results))

    @taskgraph.task_method
    def TestSolution(self, solution, ui):
        """Run tests in the problem."""
        results = yield taskgraph.TaskBranch(
            [testset.TestSolution(solution, ui) for testset in self.testsets])
        yield list(itertools.chain(*results))

    @taskgraph.task_method
    def Clean(self, ui):
        """Clean the problem."""
        ui.console.PrintAction('CLEAN', self)
        success = True
        if success:
            try:
                files.RemoveTree(self.out_dir)
            except Exception:
                ui.errors.Exception(self)
                success = False
        yield success


class ProblemComponentMixin(object):
    """Mix-in for components of a problem (solution, testset)."""

    def __init__(self):
        self.src_dir = self.base_dir
        assert self.src_dir.startswith(self.base_dir)
        rel_dir = self.src_dir[len(self.problem.base_dir) + 1:]
        self.out_dir = os.path.join(self.problem.out_dir, rel_dir)
        self.stamp_file = os.path.join(self.out_dir, consts.STAMP_FILE)

    def GetLastModified(self):
        """Get timestamp of this target."""
        stamp = files.GetLastModifiedUnder(self.src_dir)
        return stamp

    def SetCacheStamp(self, ui):
        """Update the stamp file."""
        try:
            files.CreateEmptyFile(self.stamp_file)
            return True
        except Exception:
            ui.errors.Exception(self)
            return False

    def GetCacheStamp(self):
        """Get timestamp of the stamp file.

        Returns datetime.datetime.min if not available.
        """
        return files.GetModified(self.stamp_file)

    def IsBuildCached(self):
        """Check if cached build is not staled."""
        src_mtime = self.GetLastModified()
        stamp_mtime = self.GetCacheStamp()
        return (src_mtime < stamp_mtime)


targets.registry.Add(Problem)
