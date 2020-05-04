#!/usr/bin/python

import fnmatch
import hashlib
import json
import os.path
import signal
import subprocess

from rime.basic import codes as basic_codes
from rime.basic import consts
import rime.basic.targets.problem  # NOQA
import rime.basic.targets.project  # NOQA
import rime.basic.targets.solution  # NOQA
import rime.basic.targets.testset  # NOQA
from rime.basic import test
from rime.basic.util import test_summary
from rime.core import codes
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import rime_plus_version
from rime.util import files

libdir = None


def parseVersion(v):
    return [int(d) for d in v.split('.')]


class Project(targets.registry.Project):
    def __init__(self, *args, **kwargs):
        super(Project, self).__init__(*args, **kwargs)

    def PreLoad(self, ui):
        super(Project, self).PreLoad(ui)
        self.library_dir = None
        self.project_defined = False

        def _project(library_dir=None,
                     required_rime_plus_version=rime_plus_version):
            if self.project_defined:
                # ui.errors.Error(self, 'project() is already defined.')
                raise RuntimeError('project() is already defined.')
            if (parseVersion(rime_plus_version) <
                    parseVersion(required_rime_plus_version)):
                # ui.errors.Error(self, 'installed rime-plus is too old.')
                raise RuntimeError('installed rime-plus is too old.')
            global libdir
            libdir = os.path.join(
                self.base_dir,
                library_dir)
            self.library_dir = libdir
            self.project_defined = True
        self.exports['project'] = _project


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)

    # dependency
    def PreLoad(self, ui):
        super(Testset, self).PreLoad(ui)
        self.reactives = []
        self.exports.update(
            codes.CreateDictionary('%s_generator', self.generators,
                                   src_dir=self.src_dir,
                                   out_dir=self.out_dir,
                                   wrapper=self._WrapDependency))
        self.exports.update(
            codes.CreateDictionary('%s_validator', self.validators,
                                   src_dir=self.src_dir,
                                   out_dir=self.out_dir,
                                   wrapper=self._WrapDependency))
        self.exports.update(
            codes.CreateDictionary('%s_judge', self.judges,
                                   src_dir=self.src_dir,
                                   out_dir=self.out_dir,
                                   wrapper=self._WrapDependency))
        self.exports.update(
            codes.CreateDictionary('%s_reactive', self.reactives,
                                   src_dir=self.src_dir,
                                   out_dir=self.out_dir,
                                   wrapper=self._WrapDependency))

    def _WrapDependency(self, code_class):
        def Wrapped(src_name, src_dir, out_dir, dependency=[], variant=None,
                    *args, **kwargs):
            code = code_class(src_name, src_dir, out_dir, *args, **kwargs)
            code.dependency = dependency
            code.variant = variant
            return code
        return Wrapped

    # unexpectedly accepted error message
    @taskgraph.task_method
    def _TestSolutionWithChallengeCases(self, solution, ui):
        """Test a wrong solution which has specified challenge cases."""
        all_testcases = self.ListTestCases()
        challenge_infiles = solution.challenge_cases
        testcases = []
        for infile in challenge_infiles:
            matched_testcases = [
                testcase for testcase in all_testcases
                if fnmatch.fnmatch(os.path.basename(testcase.infile), infile)]

            if not matched_testcases:
                ui.errors.Error(solution,
                                'Challenge case not found: %s' % infile)
                result = test.TestsetResult(self, solution, [])
                result.Finalize(False,
                                'Challenge case not found: %s' % infile)
                yield result

            testcases.extend(
                [t for t in matched_testcases if t.infile not in testcases])
        # Try challenge cases.
        result = test.TestsetResult(self, solution, testcases)
        yield taskgraph.TaskBranch([
            self._TestSolutionWithChallengeCasesOne(
                solution, testcase, result, ui)
            for testcase in testcases],
            unsafe_interrupt=True)
        if not result.IsFinalized():
            result.Finalize(False,
                            'Unexpectedly accepted all challenge cases')
            ui.errors.Error(solution, result.detail)
        yield result

    # input pattern & expected verdict
    @taskgraph.task_method
    def _TestSolutionWithChallengeCasesOne(self, solution, testcase, result,
                                           ui):
        """Test a wrong solution which has specified challenge cases."""
        case_result = yield self._TestOneCase(solution, testcase, ui)
        result.results[testcase] = case_result
        if (solution.expected_verdicts is None and
                case_result.verdict == test.TestCaseResult.AC):
            ui.console.PrintAction('TEST', solution,
                                   '%s: Unexpectedly accepted'
                                   % os.path.basename(testcase.infile),
                                   progress=True)
            yield False
        elif (solution.expected_verdicts is not None and
              case_result.verdict not in solution.expected_verdicts):
            result.Finalize(False,
                            '%s: Unexpected Verdict (%s)' %
                            (os.path.basename(testcase.infile),
                             case_result.verdict),
                            notable_testcase=testcase)
            ui.errors.Error(solution, result.detail)
            if ui.options.keep_going:
                yield False
            else:
                raise taskgraph.Bailout([False])
        elif case_result.verdict not in (test.TestCaseResult.WA,
                                         test.TestCaseResult.TLE,
                                         test.TestCaseResult.RE):
            result.Finalize(False,
                            '%s: Judge Error' % os.path.basename(
                                testcase.infile),
                            notable_testcase=testcase)
            ui.errors.Error(solution, result.detail)
            if ui.options.keep_going:
                yield False
            else:
                raise taskgraph.Bailout([False])
        ui.console.PrintAction('TEST', solution,
                               '%s: PASSED' % os.path.basename(
                                   testcase.infile),
                               progress=True)
        result.Finalize(True,
                        '%s: %s' % (os.path.basename(testcase.infile),
                                    case_result.verdict),
                        notable_testcase=testcase)
        yield True

    # input pattern
    @taskgraph.task_method
    def _TestSolutionWithAllCases(self, solution, ui):
        """Test a solution without challenge cases.

        The solution can be marked as wrong but without challenge cases.
        """
        testcases = self.ListTestCases()
        result = test.TestsetResult(self, solution, testcases)
        # Try all cases.
        yield taskgraph.TaskBranch([
            self._TestSolutionWithAllCasesOne(solution, testcase, result, ui)
            for testcase in testcases],
            unsafe_interrupt=True)
        if not result.IsFinalized():
            if solution.IsCorrect():
                result.Finalize(True, result.GetTimeStats(ui))
            else:
                result.Finalize(False, 'Unexpectedly accepted all test cases')
                ui.errors.Error(solution, result.detail)
        yield result

    # improve keep going & expected verdict
    @taskgraph.task_method
    def _TestSolutionWithAllCasesOne(self, solution, testcase, result, ui):
        """Test a solution without challenge cases.

        The solution can be marked as wrong but without challenge cases.
        """
        case_result = yield self._TestOneCase(solution, testcase, ui)
        result.results[testcase] = case_result
        if case_result.verdict not in (test.TestCaseResult.AC,
                                       test.TestCaseResult.WA,
                                       test.TestCaseResult.TLE,
                                       test.TestCaseResult.RE):
            result.Finalize(False,
                            '%s: Judge Error' %
                            os.path.basename(testcase.infile),
                            notable_testcase=testcase)
            ui.errors.Error(solution, result.detail)
            if ui.options.keep_going:
                yield False
            else:
                raise taskgraph.Bailout([False])
        elif case_result.verdict != test.TestCaseResult.AC:
            expected = not solution.IsCorrect()
            r = test.TestsetResult(
                result.testset, result.solution, result.testcases)
            r.Finalize(expected,
                       '%s: %s' % (os.path.basename(testcase.infile),
                                   case_result.verdict),
                       notable_testcase=testcase)
            result.Finalize(expected,
                            '%s: %s' % (os.path.basename(testcase.infile),
                                        case_result.verdict),
                            notable_testcase=testcase)
            if solution.IsCorrect():
                if case_result.verdict == test.TestCaseResult.WA:
                    judgefile = os.path.join(
                        solution.out_dir,
                        os.path.splitext(
                            os.path.basename(testcase.infile))[0] +
                        consts.JUDGE_EXT)
                    ui.errors.Error(solution,
                                    '%s\n  judge log: %s' %
                                    (r.detail, judgefile))
                else:
                    ui.errors.Error(solution, r.detail)
            elif (solution.expected_verdicts is not None and
                  case_result.verdict not in solution.expected_verdicts):
                r = test.TestsetResult(
                    result.testset, result.solution, result.testcases)
                r.Finalize(False,
                           '%s: Unexpected Verdict (%s)' %
                           (os.path.basename(testcase.infile),
                            case_result.verdict),
                           notable_testcase=testcase)
                ui.errors.Error(solution, r.detail)
                if case_result.verdict == test.TestCaseResult.WA:
                    judgefile = os.path.join(
                        solution.out_dir,
                        os.path.splitext(
                            os.path.basename(testcase.infile))[0] +
                        consts.JUDGE_EXT)
                    ui.errors.Error(solution,
                                    '%s\n  judge log: %s' %
                                    (r.detail, judgefile))
                else:
                    ui.errors.Error(solution, r.detail)
            if ui.options.keep_going:
                yield False
            else:
                raise taskgraph.Bailout([False])
        ui.console.PrintAction('TEST', solution,
                               '%s: PASSED' % os.path.basename(
                                   testcase.infile),
                               progress=True)
        yield True

    # cache test results
    @taskgraph.task_method
    def _TestOneCase(self, solution, testcase, ui):
        """Test a solution with one case.

        Cache results if option is set.
        Returns TestCaseResult.
        """
        cache_file_name = os.path.join(
            solution.out_dir,
            os.path.splitext(
                os.path.basename(testcase.infile))[0] + consts.CACHE_EXT)
        solution_file_name = os.path.join(
            solution.src_dir, solution.code.src_name)

        cache_flag = (
            ui.options.cache_tests and
            files.GetModified(solution_file_name) <
            files.GetModified(cache_file_name) and
            files.GetModified(testcase.infile) <
            files.GetModified(cache_file_name))

        if cache_flag:
            case_result_cache = files.ReadFile(cache_file_name)
            if case_result_cache is not None:
                j = json.loads(case_result_cache)
                if j['time'] is not None:
                    j['time'] = float(j['time'])
                if j['verdict'] is not None:
                    j['verdict'] = j['verdict'].encode('ascii')

                case_result = test.TestCaseResult(
                    solution, testcase, None, None, True)
                case_result.time = j['time']
                case_result.verdict = [
                    verdict for verdict in
                    test.TestCaseResult.__dict__.values()
                    if isinstance(verdict, test.TestVerdict) and
                    verdict.msg == j['verdict']][0]

            yield case_result

        case_result = yield self._TestOneCaseNoCache(solution, testcase, ui)

        # always cache in json
        files.WriteFile(json.dumps({
            'verdict': case_result.verdict.msg,
            'time': case_result.time
        }), cache_file_name)

        yield case_result

    consts.INVALID_EXT = '.invalid'
    consts.INVALIDATION_EXT = '.invalidation'

    def ListInvalidTestCases(self):
        """Enumerate invalid test cases."""
        testcases = []
        for infile in files.ListDir(self.out_dir, False):
            infile = os.path.join(self.out_dir, infile)
            if not infile.endswith(consts.INVALID_EXT):
                continue
            if not os.path.isfile(infile):
                continue
            testcases.append(test.TestCase(self, infile))
        self._SortTestCases(testcases)
        return testcases

    @taskgraph.task_method
    def _RunValidators(self, ui):
        """Run input validators."""
        if not self.validators:
            # Ignore when this testset actually does not exist.
            if self.base_dir:
                ui.errors.Warning(self, 'Validator unavailable')
            yield True
        testcases = self.ListTestCases()
        results = yield taskgraph.TaskBranch([
            self._RunValidatorOne(validator, testcase, ui)
            for validator in self.validators
            for testcase in testcases])
        if not all(results):
            yield False
        invalidcases = self.ListInvalidTestCases()
        results = yield taskgraph.TaskBranch([
            self._RunValidatorForInvalidCasesOne(validator, invalidcase, ui)
            for validator in self.validators
            for invalidcase in invalidcases])
        if not all(results):
            yield False
        ui.console.PrintAction('VALIDATE', self, 'OK')
        yield True

    @taskgraph.task_method
    def _RunValidatorForInvalidCasesOne(self, validator, testcase, ui):
        """Run an input validator against a single input file."""
        validationfile = (
            os.path.splitext(testcase.infile)[0] + consts.VALIDATION_EXT)
        res = yield validator.Run(
            args=(), cwd=self.out_dir,
            input=testcase.infile,
            output=validationfile,
            timeout=None, precise=False,
            redirect_error=True)
        if res.status == codes.RunResult.OK:
            ui.errors.Error(self,
                            '%s: Unexpectedly Validator Accepted: %s' %
                            (os.path.basename(testcase.infile), res.status))
            raise taskgraph.Bailout([False])
        ui.console.PrintAction(
            'VALIDATE', self,
            '%s: Expectedly Failed' % os.path.basename(testcase.infile),
            progress=True)
        yield True


targets.registry.Override('Project', Project)
targets.registry.Override('Testset', Testset)


# fast_test
@taskgraph.task_method
def _ExecInternal(self, args, cwd, stdin, stdout, stderr,
                  timeout=None, precise=False):
    task = taskgraph.ExternalProcessTask(
        args, cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr,
        timeout=timeout, exclusive=precise)
    proc = yield task
    code = proc.returncode
    # Retry if TLE.
    if not precise and code == -(signal.SIGXCPU):
        self._ResetIO(stdin, stdout, stderr)
        task = taskgraph.ExternalProcessTask(
            args, cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr,
            timeout=timeout, exclusive=precise)
        proc = yield task
        code = proc.returncode
    if code == 0:
        status = codes.RunResult.OK
    elif code == -(signal.SIGXCPU):
        status = codes.RunResult.TLE
    elif code < 0:
        status = codes.RunResult.RE
    else:
        status = codes.RunResult.NG
    yield codes.RunResult(status, task.time)


def IsTimingValid(self, ui):
    """Checks if timing stats are valid."""
    return (self.results and
            all((c.verdict == test.TestCaseResult.AC
                 for c in self.results.values())))


basic_codes.CodeBase._ExecInternal = _ExecInternal
test.TestsetResult.IsTimingValid = IsTimingValid


# code compile

@taskgraph.task_method
def _ExecForCompile(self, args):
    for f in files.ListDir(self.src_dir):
        srcpath = os.path.join(self.src_dir, f)
        dstpath = os.path.join(self.out_dir, f)
        if os.path.isdir(srcpath):
            files.CopyTree(srcpath, dstpath)
        else:
            files.CopyFile(srcpath, dstpath)

    if len(self.dependency) > 0:
        if libdir is None:
            raise IOError('library_dir is not defined.')
        else:
            for f in self.dependency:
                if not os.path.exists(os.path.join(libdir, f)):
                    raise IOError('%s is not found in %s.' % (f, libdir))
                files.CopyFile(
                    os.path.join(libdir, f),
                    self.out_dir)

    with open(os.path.join(self.out_dir, self.log_name), 'w') as outfile:
        yield (yield self._ExecInternal(
            args=args, cwd=self.out_dir,
            stdin=files.OpenNull(), stdout=outfile, stderr=subprocess.STDOUT))


def GetLastModified(self):
    """Get timestamp of this target."""
    stamp = files.GetLastModifiedUnder(self.src_dir)
    if self.project.library_dir is not None:
        stamp = max(stamp, files.GetLastModifiedUnder(
            self.project.library_dir))
    return stamp


basic_codes.CodeBase._ExecForCompile = _ExecForCompile
basic_codes.CodeBase.dependency = []
basic_codes.CodeBase.variant = None
rime.basic.targets.problem.ProblemComponentMixin.GetLastModified = \
    GetLastModified


# -O2
class CCode(codes.registry.CCode):
    def __init__(self, src_name, src_dir, out_dir, flags=['-lm']):
        super(CCode, self).__init__(
            src_name, src_dir, out_dir, ['-O2'] + flags)


class CXXCode(codes.registry.CXXCode):
    EXTENSIONS = ['cc', 'cxx', 'cpp']

    def __init__(self, src_name, src_dir, out_dir, flags=[]):
        super(CXXCode, self).__init__(
            src_name, src_dir, out_dir, ['-std=c++11', '-O2'] + flags)


# -C opt-level=2
class RustCode(codes.registry.RustCode):
    def __init__(self, src_name, src_dir, out_dir, flags=[]):
        super(RustCode, self).__init__(
            src_name, src_dir, out_dir, ['-C', 'opt-level=2'] + flags)


# shebang support
# codes.registry.ScriptCode is not supported
class ScriptCode(basic_codes.ScriptCode):
    def __init__(self, src_name, src_dir, out_dir, run_flags=[]):
        super(ScriptCode, self).__init__(src_name, src_dir, out_dir, run_flags)
        # Replace the executable with the shebang line
        run_args = list(self.run_args)
        try:
            run_args[0] = self._ReadAndParseShebangLine()
            if run_args[0] is not None:
                run_args = run_args[0].split(' ') + run_args[1:]
        except IOError:
            pass
        self.run_args = tuple(run_args)

    @taskgraph.task_method
    def Compile(self, *args, **kwargs):
        """Fail if the script is missing a shebang line."""
        try:
            interpreter = self.run_args[0]
        except IOError:
            yield codes.RunResult('File not found', None)
        if not interpreter:
            yield codes.RunResult('Script missing a shebang line', None)
        if not os.path.exists(interpreter):
            yield codes.RunResult('Interpreter not found: %s' %
                                  interpreter, None)

        # when using env, try to output more detailed error message
        if interpreter == '/bin/env' or interpreter == '/usr/bin/env':
            try:
                # if the command does not exist,
                # "which" return 1 as the status code
                interpreter = subprocess.check_output(
                    ['which', self.run_args[1]]).strip()
            except subprocess.CalledProcessError:
                yield codes.RunResult(
                    'Interpreter not installed: %s' % self.run_args[1], None)
            if not os.path.exists(interpreter):
                yield codes.RunResult('Interpreter not found: %s' %
                                      interpreter, None)

        yield (yield basic_codes.CodeBase.Compile(self, *args, **kwargs))


codes.registry.Override('CCode', CCode)
codes.registry.Override('CXXCode', CXXCode)
codes.registry.Override('RustCode', RustCode)
codes.registry.Override('ScriptCode', ScriptCode)


# thanks to Klab
class JavaScriptCode(basic_codes.CodeBase):
    QUIET_COMPILE = True
    PREFIX = 'js'
    EXTENSIONS = ['js']

    def __init__(self, src_name, src_dir, out_dir, run_flags=[]):
        super(JavaScriptCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=[],
            run_args=['node', '--',
                      os.path.join(src_dir, src_name)] + run_flags)

    @taskgraph.task_method
    def Compile(self, *args, **kwargs):
        """Fail if the script is missing a shebang line."""
        try:
            open(os.path.join(self.src_dir, self.src_name))
        except IOError:
            yield codes.RunResult('File not found', None)
        yield (yield super(JavaScriptCode, self).Compile(*args, **kwargs))


class HaskellCode(basic_codes.CodeBase):
    PREFIX = 'hs'
    EXTENSIONS = ['hs']

    def __init__(self, src_name, src_dir, out_dir, flags=[]):
        exe_name = os.path.splitext(src_name)[0] + consts.EXE_EXT
        exe_path = os.path.join(out_dir, exe_name)
        super(HaskellCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=(['stack', 'ghc', '--', '-O',
                           '-o', exe_path, '-outputdir', out_dir, src_name] +
                          list(flags)),
            run_args=[exe_path])


class CsCode(basic_codes.CodeBase):
    PREFIX = 'cs'
    EXTENSIONS = ['cs']

    def __init__(self, src_name, src_dir, out_dir, flags=[]):
        exe_name = os.path.splitext(src_name)[0] + consts.EXE_EXT
        exe_path = os.path.join(out_dir, exe_name)
        super(CsCode, self).__init__(
            src_name=src_name,
            src_dir=src_dir,
            out_dir=out_dir,
            compile_args=(['mcs',
                           src_name,
                           '-out:' + exe_path] + list(flags)),
            run_args=['mono', exe_path])


codes.registry.Add(CsCode)
codes.registry.Add(JavaScriptCode)
codes.registry.Add(HaskellCode)


# Summary

def PrintTestSummary(results, ui):
    if len(results) == 0:
        return

    PrintBuildSummary(results, ui)

    ui.console.Print()
    ui.console.Print(ui.console.BOLD, 'Test Summary:', ui.console.NORMAL)
    solution_name_width = max(
        map(lambda t: len(t.solution.name), results))
    last_problem = None
    for result in sorted(results, key=_KeyTestResultForListing):
        if last_problem is not result.problem:
            problem_row = [
                ui.console.BOLD,
                ui.console.CYAN,
                result.problem.name,
                ui.console.NORMAL,
                ' ... %d solutions, %d tests' %
                (len(result.problem.solutions),
                 len(result.problem.testset.ListTestCases()))]
            ui.console.Print(*problem_row)
            last_problem = result.problem
        status_row = ['  ']
        status_row += [
            result.solution.IsCorrect() and ui.console.GREEN
            or ui.console.YELLOW,
            result.solution.name.ljust(solution_name_width),
            ui.console.NORMAL,
            ' ']
        if result.expected:
            status_row += [ui.console.GREEN, ' OK ', ui.console.NORMAL]
        else:
            status_row += [ui.console.RED, 'FAIL', ui.console.NORMAL]
        status_row += [' ', result.detail]
        if result.IsCached():
            status_row += [' ', '(cached)']
        ui.console.Print(*status_row)


def PrintBuildSummary(results, ui):
    if len(results) == 0:
        return
    ui.console.Print()
    ui.console.Print(ui.console.BOLD, 'Build Summary:', ui.console.NORMAL)
    solution_name_width = max(
        map(lambda t: len(t.solution.name), results))
    solution_prefix_width = max(
        map(lambda t: len(t.solution.code.PREFIX), results))
    solution_line_width = max(
        map(lambda t: len(_SolutionLine(t.solution)), results))
    solution_size_width = max(
        map(lambda t: len(_SolutionSize(t.solution)), results))
    last_problem = None
    for result in sorted(results, key=_KeyTestResultForListing):
        if last_problem is not result.problem:
            problem_row = [
                ui.console.BOLD,
                ui.console.CYAN,
                result.problem.name,
                ui.console.NORMAL,
                ' ... in: %s, diff: %s, md5: %s' %
                (_TestsetInSize(result),
                 _TestsetDiffSize(result),
                 _TestsetHash(result)
                 )]
            ui.console.Print(*problem_row)
            last_problem = result.problem
        status_row = ['  ']
        status_row += [
            result.solution.IsCorrect() and ui.console.GREEN
            or ui.console.YELLOW,
            result.solution.name.ljust(solution_name_width),
            ' ',
            ui.console.GREEN,
            result.solution.code.PREFIX.upper().ljust(solution_prefix_width),
            ' ',
            ui.console.NORMAL,
            _SolutionLine(result.solution).rjust(solution_line_width),
            ', ',
            _SolutionSize(result.solution).rjust(solution_size_width)]
        ui.console.Print(*status_row)


def _TestsetHash(result):
    try:
        md5 = hashlib.md5()
        for t in result.problem.testset.ListTestCases():
            md5.update(files.ReadFile(t.infile))
        return md5.hexdigest()
    except Exception:
        return '-'


def _TestsetInSize(result):
    try:
        size = 0
        for t in result.problem.testset.ListTestCases():
            size += len(files.ReadFile(t.infile))
        return _SmartFileSize(size)
    except Exception:
        return '-'


def _TestsetDiffSize(result):
    try:
        size = 0
        for t in result.problem.testset.ListTestCases():
            out_file = os.path.join(
                result.problem.testset.out_dir,
                os.path.splitext(os.path.basename(t.infile))[0]
                + consts.DIFF_EXT)
            size += len(files.ReadFile(out_file))
        return _SmartFileSize(size)
    except Exception:
        return '-'


def _SolutionSize(solution):
    try:
        src = os.path.join(solution.src_dir, solution.code.src_name)
        return _SmartFileSize(len(files.ReadFile(src)))
    except Exception:
        return '-'


def _SolutionLine(solution):
    try:
        src = os.path.join(solution.src_dir, solution.code.src_name)
        return str(sum(1 for line in open(src))) + ' lines'
    except Exception:
        return '-'


def _SmartFileSize(size):
    if size < 1000:
        return str(size) + 'B'
    elif size < 1000000:
        return '{:.1f}kB'.format(size / 1000.0)
    else:
        return '{:.1f}MB'.format(size / 1000000.0)


# sort correctly
def _KeyTestResultForListing(a):
    """Key function of TestResult for display-ordering."""
    return (a.problem.id, test_summary.KeyTestResultForListing(a))


test_summary.PrintBuildSummary = PrintBuildSummary
test_summary.PrintTestSummary = PrintTestSummary


# expected verdict
class Solution(targets.registry.Solution):
    def __init__(self, *args, **kwargs):
        super(Solution, self).__init__(*args, **kwargs)
        self.expected_verdicts = None

    def PreLoad(self, ui):
        super(Solution, self).PreLoad(ui)

        def expected_verdicts(verdicts):
            self.expected_verdicts = verdicts
        self.exports['expected_verdicts'] = expected_verdicts

        self.exports['AC'] = test.TestCaseResult.AC
        self.exports['WA'] = test.TestCaseResult.WA
        self.exports['TLE'] = test.TestCaseResult.TLE
        self.exports['RE'] = test.TestCaseResult.RE


targets.registry.Override('Solution', Solution)
