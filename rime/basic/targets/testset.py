#!/usr/bin/python
#
# Copyright (c) 2011 Rime Project.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import itertools
import os.path
import re

from rime.basic import codes as basic_codes
from rime.basic import consts
from rime.basic import results
from rime.basic.targets import problem
from rime.core import codes as core_codes
from rime.core import targets
from rime.core import taskgraph
from rime.util import files


class Testset(targets.TargetBase, problem.ProblemComponentMixin):
  """Testset target."""

  CONFIG_FILENAME = 'TESTSET'

  def __init__(self, name, base_dir, parent):
    assert isinstance(parent, problem.Problem)
    super(Testset, self).__init__(name, base_dir, parent)
    self.project = parent.project
    self.problem = parent
    problem.ProblemComponentMixin.__init__(self)

  @classmethod
  def CreateEmpty(cls, parent, ui):
    # Workaround for no testset case.
    # TODO(nya): support multiple testsets.
    testset = cls('tests', '', parent)
    testset.config_file = '/dev/null'
    testset.Load(ui)
    return testset

  def PreLoad(self, ui):
    super(Testset, self).PreLoad(ui)
    self.generators = []
    self.validators = []
    self.judges = []
    self.exports.update(
      core_codes.CreateDictionary('%s_generator', self.generators,
                                  src_dir=self.src_dir,
                                  out_dir=self.out_dir))
    self.exports.update(
      core_codes.CreateDictionary('%s_validator', self.validators,
                                  src_dir=self.src_dir,
                                  out_dir=self.out_dir))
    self.exports.update(
      core_codes.CreateDictionary('%s_judge', self.judges,
                                  src_dir=self.src_dir,
                                  out_dir=self.out_dir))

  def PostLoad(self, ui):
    if not self.judges:
      self.judges.append(basic_codes.InternalDiffCode())

  def GetLastModified(self):
    """Get timestamp of this target.

    Testsets depend on reference solution.
    """
    stamp = problem.ProblemComponentMixin.GetLastModified(self)
    if self.problem.reference_solution:
      stamp = max(stamp, self.problem.reference_solution.GetLastModified())
    return stamp

  def ListInputFiles(self):
    """Enumerate input files."""
    infiles = []
    for infile in files.ListDir(self.out_dir, True):
      if not infile.endswith(consts.IN_EXT):
        continue
      if not os.path.isfile(os.path.join(self.out_dir, infile)):
        continue
      infiles.append(infile)
    infiles = self._SortInputFiles(infiles)
    return infiles

  def _SortInputFiles(self, infiles):
    """Compare input file names in a little bit smart way."""
    infiles = infiles[:]
    def tokenize_cmp(a, b):
      def tokenize(s):
        def replace_digits(match):
          return '%08s' % match.group(0)
        return re.sub(r'\d+', replace_digits, s)
      return cmp(tokenize(a), tokenize(b))
    infiles.sort(tokenize_cmp)
    return infiles

  @taskgraph.task_method
  def Build(self, ui):
    """Build testset."""
    if self.IsBuildCached():
      if not self.ListInputFiles():
        ui.errors.Warning(self, 'No test case found')
      yield True
    if not self._InitOutputDir(ui):
      yield False
    if not all((yield taskgraph.TaskBranch([
            self._CompileGenerators(ui),
            self._CompileValidators(ui),
            self._CompileJudges(ui)]))):
      yield False
    if not (yield self._RunGenerators(ui)):
      yield False
    if not (yield self._RunValidators(ui)):
      yield False
    if not self.ListInputFiles():
      ui.errors.Warning(self, 'No test case found')
    else:
      if not (yield self._CompileReferenceSolution(ui)):
        yield False
      if not (yield self._RunReferenceSolution(ui)):
        yield False
    if not self.SetCacheStamp(ui):
      yield False
    yield True

  def _InitOutputDir(self, ui):
    """Initialize output directory."""
    try:
      files.RemoveTree(self.out_dir)
      files.CopyTree(self.src_dir, self.out_dir)
      return True
    except:
      ui.errors.Exception(self)
      return False

  @taskgraph.task_method
  def _CompileGenerators(self, ui):
    """Compile all input generators."""
    results = yield taskgraph.TaskBranch([
        self._CompileGeneratorOne(generator, ui)
        for generator in self.generators])
    yield all(results)

  @taskgraph.task_method
  def _CompileGeneratorOne(self, generator, ui):
    """Compile a single input generator."""
    if not generator.QUIET_COMPILE:
      ui.console.PrintAction('COMPILE', self, generator.src_name)
    res = yield generator.Compile()
    if res.status != core_codes.RunResult.OK:
      ui.errors.Error(self,
                      '%s: Compile Error (%s)' % (generator.src_name, res.status))
      ui.console.PrintLog(generator.ReadCompileLog())
      raise taskgraph.Bailout([False])
    yield True

  @taskgraph.task_method
  def _RunGenerators(self, ui):
    """
    Run all input generators.
    """
    results = yield taskgraph.TaskBranch([
        self._RunGeneratorOne(generator, ui)
        for generator in self.generators])
    yield all(results)

  @taskgraph.task_method
  def _RunGeneratorOne(self, generator, ui):
    """
    Run a single input generator.
    """
    ui.console.PrintAction('GENERATE', self, generator.src_name)
    res = yield generator.Run(
      args=(), cwd=self.out_dir,
      input=os.devnull, output=os.devnull, timeout=None, precise=False)
    if res.status != core_codes.RunResult.OK:
      ui.errors.Error(self,
                      '%s: %s' % (generator.src_name, res.status))
      raise taskgraph.Bailout([False])
    yield True

  @taskgraph.task_method
  def _CompileValidators(self, ui):
    """
    Compile input validators.
    """
    results = yield taskgraph.TaskBranch([
        self._CompileValidatorOne(validator, ui)
        for validator in self.validators])
    yield all(results)

  @taskgraph.task_method
  def _CompileValidatorOne(self, validator, ui):
    """
    Compile a single input validator.
    """
    if not validator.QUIET_COMPILE:
      ui.console.PrintAction('COMPILE', self, validator.src_name)
    res = yield validator.Compile()
    if res.status != core_codes.RunResult.OK:
      ui.errors.Error(self,
                      '%s: Compile Error (%s)' % (validator.src_name, res.status))
      ui.console.PrintLog(validator.ReadCompileLog())
      raise taskgraph.Bailout([False])
    yield True

  @taskgraph.task_method
  def _RunValidators(self, ui):
    """
    Run input validators.
    """
    if not self.validators:
      # Ignore when this testset actually does not exist.
      if self.base_dir:
        #ui.console.PrintAction('VALIDATE', self, 'skipping: validator unavailable')
        ui.errors.Warning(self, 'Validator unavailable')
      yield True
    infiles = self.ListInputFiles()
    results = yield taskgraph.TaskBranch([
        self._RunValidatorOne(validator, infile, ui)
        for validator in self.validators
        for infile in infiles])
    if not all(results):
      yield False
    ui.console.PrintAction('VALIDATE', self, 'OK')
    yield True

  @taskgraph.task_method
  def _RunValidatorOne(self, validator, infile, ui):
    """
    Run an input validator against a single input file.
    """
    #ui.console.PrintAction('VALIDATE', self,
    #                        infile, progress=True)
    validationfile = os.path.splitext(infile)[0] + consts.VALIDATION_EXT
    res = yield validator.Run(
      args=(), cwd=self.out_dir,
      input=os.path.join(self.out_dir, infile),
      output=os.path.join(self.out_dir, validationfile),
      timeout=None, precise=False,
      redirect_error=True)
    if res.status == core_codes.RunResult.NG:
      ui.errors.Error(self,
                      '%s: Validation Failed' % infile)
      log = files.ReadFile(os.path.join(self.out_dir, validationfile))
      ui.console.PrintLog(log)
      raise taskgraph.Bailout([False])
    elif res.status != core_codes.RunResult.OK:
      ui.errors.Error(self,
                      '%s: Validator Failed: %s' % (infile, res.status))
      raise taskgraph.Bailout([False])
    ui.console.PrintAction('VALIDATE', self,
                            '%s: PASSED' % infile, progress=True)
    yield True

  @taskgraph.task_method
  def _CompileJudges(self, ui):
    """Compile all judges."""
    results = yield taskgraph.TaskBranch([
        self._CompileJudgeOne(judge, ui)
        for judge in self.judges])
    yield all(results)

  @taskgraph.task_method
  def _CompileJudgeOne(self, judge, ui):
    """Compile a single judge."""
    if not judge.QUIET_COMPILE:
      ui.console.PrintAction('COMPILE', self, judge.src_name)
    res = yield judge.Compile()
    if res.status != core_codes.RunResult.OK:
      ui.errors.Error(self, '%s: Compile Error (%s)' % (judge.src_name, res.status))
      ui.console.PrintLog(judge.ReadCompileLog())
      yield False
    yield True

  @taskgraph.task_method
  def _CompileReferenceSolution(self, ui):
    """Compile the reference solution."""
    reference_solution = self.problem.reference_solution
    if reference_solution is None:
      ui.errors.Error(self, 'Reference solution unavailable')
      yield False
    yield (yield reference_solution.Build(ui))

  @taskgraph.task_method
  def _RunReferenceSolution(self, ui):
    """
    Run the reference solution to generate reference outputs.
    """
    reference_solution = self.problem.reference_solution
    if reference_solution is None:
      ui.errors.Error(self, 'Reference solution unavailable')
      yield False
    infiles = self.ListInputFiles()
    results = yield taskgraph.TaskBranch([
        self._RunReferenceSolutionOne(reference_solution, infile, ui)
        for infile in infiles])
    if not all(results):
      yield False
    ui.console.PrintAction('REFRUN', reference_solution)
    yield True

  @taskgraph.task_method
  def _RunReferenceSolutionOne(self, reference_solution, infile, ui):
    """
    Run the reference solution against a single input file.
    """
    difffile = os.path.splitext(infile)[0] + consts.DIFF_EXT
    if os.path.isfile(os.path.join(self.out_dir, difffile)):
      yield True
    #ui.console.PrintAction('REFRUN', reference_solution,
    #                        infile, progress=True)
    res = yield reference_solution.Run(
      args=(), cwd=self.out_dir,
      input=os.path.join(self.out_dir, infile),
      output=os.path.join(self.out_dir, difffile),
      timeout=None, precise=False)
    if res.status != core_codes.RunResult.OK:
      ui.errors.Error(reference_solution, res.status)
      raise taskgraph.Bailout([False])
    ui.console.PrintAction('REFRUN', reference_solution,
                            '%s: DONE' % infile, progress=True)
    yield True

  @taskgraph.task_method
  def Test(self, ui):
    """Run tests in the testset."""
    results = yield taskgraph.TaskBranch(
      [self.TestSolution(solution, ui) for solution in self.problem.solutions])
    yield list(itertools.chain(*results))

  @taskgraph.task_method
  def TestSolution(self, solution, ui):
    """Test a single solution."""
    if not (yield self.Build(ui)):
      result = results.TestResult(self.problem, solution, [])
      result.good = False
      result.passed = False
      result.detail = 'Failed to build tests'
      yield [result]
    if not (yield solution.Build(ui)):
      result = results.TestResult(self.problem, solution, [])
      result.good = False
      result.passed = False
      result.detail = 'Compile Error'
      yield [result]
    ui.console.PrintAction('TEST', solution, progress=True)
    if not solution.IsCorrect() and solution.challenge_cases:
      result = yield self._TestSolutionWithChallengeCases(solution, ui)
    else:
      result = yield self._TestSolutionWithAllCases(solution, ui)
    if result.good and result.passed:
      assert not result.detail
      if result.IsTimeStatsAvailable(ui):
        result.detail = result.GetTimeStats()
      else:
        result.detail = '(*/*)'
    else:
      assert result.detail
    status_row = []
    status_row += [
      result.good and ui.console.CYAN or ui.console.RED,
      result.passed and 'PASSED' or 'FAILED',
      ui.console.NORMAL,
      ' ',
      result.detail]
    if result.cached:
      status_row += [' ', '(cached)']
    ui.console.PrintAction('TEST', solution, *status_row)
    if solution.IsCorrect() and not result.good:
      assert result.ruling_file
      judgefile = os.path.splitext(result.ruling_file)[0] + consts.JUDGE_EXT
      log = files.ReadFile(os.path.join(solution.out_dir, judgefile))
      ui.console.PrintLog(log)
    yield [result]

  @taskgraph.task_method
  def _TestSolutionWithChallengeCases(self, solution, ui):
    """Test a wrong solution which has explicitly-specified challenge cases."""
    infiles = self.ListInputFiles()
    challenge_cases = self._SortInputFiles(solution.challenge_cases)
    result = results.TestResult(self.problem, solution, challenge_cases)
    # Ensure all challenge cases exist.
    all_exists = True
    for infile in challenge_cases:
      if infile not in infiles:
        ui.errors.Error(solution,
                        'Challenge case not found: %s' % infile)
        all_exists = False
    if not all_exists:
      result.good = False
      result.passed = False
      result.detail = 'Challenge case not found'
      yield result
    # Try challenge cases.
    yield taskgraph.TaskBranch([
        self._TestSolutionWithChallengeCasesOne(solution, infile, result, ui)
        for infile in challenge_cases],
        unsafe_interrupt=True)
    if result.good is None:
      result.good = True
      result.passed = False
      result.detail = 'Expectedly Failed'
    yield result

  @taskgraph.task_method
  def _TestSolutionWithChallengeCasesOne(self, solution, infile, result, ui):
    """Test a wrong solution which has explicitly-specified challenge cases."""
    cookie = solution.GetCacheStamp()
    # TODO(nya): Concat support
    #ignore_timeout = (infile == consts.CONCAT_INFILE)
    ignore_timeout = False
    (verdict, time, cached) = yield self._TestOneCase(
      solution, infile, cookie, ignore_timeout, ui)
    if cached:
      result.cached = True
    result.cases[infile].verdict = verdict
    if verdict == results.TestResult.AC:
      result.ruling_file = infile
      result.good = False
      result.passed = True
      result.detail = '%s: Unexpectedly Accepted' % infile
      ui.errors.Error(solution, result.detail)
      if ui.options.keep_going:
        yield False
      else:
        raise taskgraph.Bailout([False])
    elif verdict not in (results.TestResult.WA,
                         results.TestResult.TLE,
                         results.TestResult.RE):
      result.ruling_file = infile
      result.good = False
      result.passed = False
      result.detail = '%s: Judge Error' % infile
      ui.errors.Error(solution, result.detail)
      if ui.options.keep_going:
        yield False
      else:
        raise taskgraph.Bailout([False])
    ui.console.PrintAction('TEST', solution,
                            '%s: PASSED' % infile, progress=True)
    yield True

  @taskgraph.task_method
  def _TestSolutionWithAllCases(self, solution, ui):
    """Test a solution without challenge cases.

    The solution can be marked as wrong but without challenge cases.
    """
    infiles = self.ListInputFiles()
    result = results.TestResult(self.problem, solution, infiles)
    # Try all cases.
    yield taskgraph.TaskBranch([
        self._TestSolutionWithAllCasesOne(solution, infile, result, ui)
        for infile in infiles],
        unsafe_interrupt=True)
    if result.good is None:
      result.good = solution.IsCorrect()
      result.passed = True
      if not result.good:
        result.detail = 'Unexpectedly Passed'
    yield result

  @taskgraph.task_method
  def _TestSolutionWithAllCasesOne(self, solution, infile, result, ui):
    """Test a solution without challenge cases.

    The solution can be marked as wrong but without challenge cases.
    """
    cookie = solution.GetCacheStamp()
    # TODO(nya): Concat support
    #ignore_timeout = (infile == consts.CONCAT_INFILE)
    ignore_timeout = False
    (verdict, time, cached) = yield self._TestOneCase(
      solution, infile, cookie, ignore_timeout, ui)
    if cached:
      result.cached = True
    result.cases[infile].verdict = verdict
    if verdict not in (results.TestResult.AC,
                       results.TestResult.WA,
                       results.TestResult.TLE,
                       results.TestResult.RE):
      result.ruling_file = infile
      result.good = False
      result.passed = False
      result.detail = '%s: Judge Error' % infile
      ui.errors.Error(solution, result.detail)
      if ui.options.keep_going:
        yield False
      else:
        raise taskgraph.Bailout([False])
    elif verdict != results.TestResult.AC:
      result.ruling_file = infile
      result.passed = False
      result.detail = '%s: %s' % (infile, verdict)
      if solution.IsCorrect():
        result.good = False
        ui.errors.Error(solution, result.detail)
      else:
        result.good = True
      if ui.options.keep_going:
        yield False
      else:
        raise taskgraph.Bailout([False])
    result.cases[infile].time = time
    ui.console.PrintAction('TEST', solution,
                            '%s: PASSED' % infile, progress=True)
    yield True

  @taskgraph.task_method
  def _TestOneCase(self, solution, infile, cookie, ignore_timeout, ui):
    """Test a solution with one case.

    Cache results if option is set.
    Return (verdict, time, cached).
    """
    cachefile = os.path.join(
      solution.out_dir,
      os.path.splitext(infile)[0] + consts.CACHE_EXT)
    if ui.options.cache_tests:
      if cookie is not None and os.path.isfile(cachefile):
        try:
          (cached_cookie, result) = files.PickleLoad(cachefile)
        except:
          ui.errors.Exception(solution)
          cached_cookie = None
        if cached_cookie == cookie:
          yield tuple(list(result)+[True])
    result = yield self._TestOneCaseNoCache(solution, infile, ignore_timeout, ui)
    try:
      files.PickleSave((cookie, result), cachefile)
    except:
      ui.errors.Exception(solution)
    yield tuple(list(result)+[False])

  @taskgraph.task_method
  def _TestOneCaseNoCache(self, solution, infile, ignore_timeout, ui):
    """Test a solution with one case.

    Never cache results.
    Return (verdict, time).
    """
    outfile = os.path.splitext(infile)[0] + consts.OUT_EXT
    difffile = os.path.splitext(infile)[0] + consts.DIFF_EXT
    judgefile = os.path.splitext(infile)[0] + consts.JUDGE_EXT
    timeout = self.problem.timeout
    if ignore_timeout:
      timeout = None
    precise = (ui.options.precise or ui.options.parallelism <= 1)
    res = yield solution.Run(
      args=(), cwd=solution.out_dir,
      input=os.path.join(self.out_dir, infile),
      output=os.path.join(solution.out_dir, outfile),
      timeout=timeout, precise=precise)
    if res.status == core_codes.RunResult.TLE:
      yield (results.TestResult.TLE, None)
    if res.status != core_codes.RunResult.OK:
      yield (results.TestResult.RE, None)
    time = res.time
    for judge in self.judges:
      res = yield judge.Run(
        args=('--infile', os.path.join(self.out_dir, infile),
              '--difffile', os.path.join(self.out_dir, difffile),
              '--outfile', os.path.join(solution.out_dir, outfile)),
        cwd=self.out_dir,
        input=os.devnull,
        output=os.path.join(solution.out_dir, judgefile),
        timeout=None, precise=False)
      if res.status == core_codes.RunResult.NG:
        yield (results.TestResult.WA, None)
      elif res.status != core_codes.RunResult.OK:
        yield ('Validator ' + res.status, None)
    yield (results.TestResult.AC, time)

  @taskgraph.task_method
  def Clean(self, ui):
    """Clean the testset."""
    ui.console.PrintAction('CLEAN', self)
    try:
      files.RemoveTree(self.out_dir)
    except:
      ui.errors.Exception(self)
    yield True


targets.registry.Add(Testset)
