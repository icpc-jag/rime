#!/usr/bin/python

import os
import os.path
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import requests

from rime.basic import codes as basic_codes
from rime.basic import consts, test
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import commands as plus_commands
from rime.plugins.plus import flexible_judge
from rime.util import files


class Project(targets.registry.Project):
    def PreLoad(self, ui):
        super(Project, self).PreLoad(ui)
        self.domjudge_config_defined = False

        def _domjudge_config(url, contest_id, username, password):
            self.domjudge_config_defined = True
            self.domjudge_url = url
            self.domjudge_contest_id = contest_id
            self.domjudge_username = username
            self.domjudge_password = password
        self.exports['domjudge_config'] = _domjudge_config


class Problem(targets.registry.Problem):
    def PreLoad(self, ui):
        super(Problem, self).PreLoad(ui)
        self.domjudge_config_defined = False

        def _domjudge_config(problem_file=None, color=None):
            self.domjudge_config_defined = True
            self.domjudge_problem_file = problem_file
            self.domjudge_color = color
        self.exports['domjudge_config'] = _domjudge_config


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.domjudge_pack_dir = os.path.join(self.problem.out_dir, 'domjudge')


class DOMJudgeJudgeRunner(flexible_judge.JudgeRunner):
    PREFIX = 'domjudge'

    def Run(self, judge, infile, difffile, outfile, cwd, judgefile):
        domjudge_workdir = infile + '.domjudge'
        files.MakeDir(domjudge_workdir)
        return judge.Run(
            args=(infile, difffile, domjudge_workdir),
            cwd=cwd,
            input=outfile,
            output=judgefile,
            timeout=None, precise=False,
            redirect_error=True,
            ok_returncode=42, ng_returncode=43)


class DOMJudgeReactiveTask(taskgraph.Task):
    def __init__(self, judge_args, solution_args, **kwargs):
        self.judge_args = judge_args
        self.solution_args = solution_args
        self.judge_proc = None
        self.solution_proc = None
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        else:
            self.timeout = None
        if 'exclusive' in kwargs:
            self.exclusive = kwargs['exclusive']
            del kwargs['exclusive']
        else:
            self.exclusive = False
        self.kwargs = kwargs
        self.timer = None

    def CacheKey(self):
        # Never cache.
        return None

    def IsExclusive(self):
        return self.exclusive

    def Continue(self, value=None):
        if self.exclusive:
            return self._ContinueExclusive()
        else:
            return self._ContinueNonExclusive()

    def _ContinueExclusive(self):
        assert self.judge_proc is None
        assert self.solution_proc is None
        self._StartProcess()
        self.judge_proc.wait()
        self.solution_proc.wait()
        return taskgraph.TaskReturn(self._EndProcess())

    def _ContinueNonExclusive(self):
        if self.judge_proc is None:
            self._StartProcess()
            return taskgraph.TaskBlock()
        elif not self.Poll():
            return taskgraph.TaskBlock()
        else:
            return taskgraph.TaskReturn(self._EndProcess())

    def Poll(self):
        assert self.judge_proc is not None
        return self.judge_proc.poll() is not None

    def Wait(self):
        assert self.judge_proc is not None
        self.judge_proc.wait()

    def Close(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        if self.judge_proc is not None:
            try:
                os.kill(self.judge_proc.pid, signal.SIGKILL)
            except Exception:
                pass
            self.judge_proc.wait()
            self.judge_proc = None
        if self.solution_proc is not None:
            try:
                os.kill(self.solution_proc.pid, signal.SIGKILL)
            except Exception:
                pass
            self.solution_proc.wait()
            self.solution_proc = None

    def _StartProcess(self):
        self.start_time = time.time()
        self.judge_proc = subprocess.Popen(self.judge_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, **self.kwargs)
        self.solution_proc = subprocess.Popen(self.solution_args, stdin=self.judge_proc.stdout, stdout=self.judge_proc.stdin, **self.kwargs)
        # finishing judge_proc will make pipes closed, but solution_proc doesn't.
        # Let's watch solution_proc in a separate thread and close pipes.
        def run_in_thread():
            self.solution_proc.wait()
            if self.judge_proc is None:
                return
            if self.judge_proc.stdin is not None:
                self.judge_proc.stdin.close()
            if self.judge_proc.stdout is not None:
                self.judge_proc.stdout.close()
        thread = threading.Thread(target=run_in_thread)
        thread.start()

        if self.timeout is not None:
            def TimeoutKiller():
                try:
                    os.kill(self.solution_proc.pid, signal.SIGXCPU)
                    os.kill(self.judge_proc.pid, signal.SIGXCPU)
                except Exception:
                    pass
            self.timer = threading.Timer(self.timeout, TimeoutKiller)
            self.timer.start()
        else:
            self.timer = None

    def _EndProcess(self):
        self.end_time = time.time()
        self.time = self.end_time - self.start_time
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        # Don't keep proc in cache.
        judge_proc = self.judge_proc
        # TODO call terminate() or something if any of them are still alive?
        self.judge_proc = None
        self.solution_proc = None
        return judge_proc


class DOMJudgeReactiveRunner(flexible_judge.ReactiveRunner):
    PREFIX = 'domjudge'

    @taskgraph.task_method
    def Run(self, reactive, args, cwd, input, output, timeout, precise):
        # TODO instead of tmpfile, store log somewhere.
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.NamedTemporaryFile() as tmpfile:
                judge_args = reactive.run_args + (input, tmpfile.name, tmpdir, )
                solution_args = args
                proc = yield DOMJudgeReactiveTask(
                    judge_args, solution_args,
                    cwd=cwd, timeout=timeout, exclusive=precise)
                code = proc.returncode
                # TODO Report error on judge process and solution process differently:
                if code == 42:
                    yield test.TestCaseResult.AC
                if code == 43:
                    yield test.TestCaseResult.AC
                elif code == -(signal.SIGXCPU):
                    yield test.TestCaseResult.TLE
                elif code < 0:
                    yield test.TestCaseResult.RE
                else:
                    yield test.TestCaseResult.ERR

            for filename in os.listdir(tmpdir):
                if os.path.isfile(os.path.join(tmpdir, filename)):
                    with open(os.path.join(tmpdir, filename), 'r') as f:
                        print('file' + filename)
                        print(f.read())
                        print()


class DOMJudgePacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        pack_files_dir = os.path.join(testset.domjudge_pack_dir, 'files')
        try:
            files.RemoveTree(testset.domjudge_pack_dir)
            files.MakeDir(os.path.join(pack_files_dir, 'data', 'sample'))
            files.MakeDir(os.path.join(pack_files_dir, 'data', 'secret'))

            # Generate domjudge-problem.ini
            ini_file = os.path.join(pack_files_dir, 'domjudge-problem.ini')
            with open(ini_file, 'w') as f:
                f.write(f'externalid = "{testset.problem.name}"\n')
                f.write(f'short-name = "{testset.problem.id}"\n')
                f.write(f'name = "{testset.problem.title}"\n')
                f.write(f'timelimit = {testset.problem.timeout}\n')
                if (testset.problem.domjudge_config_defined and
                        testset.problem.domjudge_color):
                    f.write(f'color = {testset.problem.domjudge_color}\n')
        except Exception:
            ui.errors.Exception(testset)
            yield False

        testcases = testset.ListTestCases()
        for (i, testcase) in enumerate(testcases):
            basename = os.path.splitext(os.path.basename(testcase.infile))[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile = basename + ".in"
            packed_difffile = basename + ".ans"
            is_sample = 'sample' in packed_infile
            target_dir = os.path.join(
                pack_files_dir, 'data',
                'sample' if is_sample else 'secret')

            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(testcase.infile),
                                  packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(target_dir, packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(difffile), packed_difffile),
                    progress=True)
                files.CopyFile(
                    os.path.join(testset.out_dir, testcase.difffile),
                    os.path.join(target_dir, packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        if len(testset.judges) > 1:
            ui.errors.Error(
                testset, 'Multiple varidators is not supported in DOMJudge.')
            yield False
        elif (len(testset.judges) == 1 and
                not isinstance(testset.judges[0], basic_codes.InternalDiffCode)):
            judge = testset.judges[0]

            if not isinstance(judge.variant, DOMJudgeJudgeRunner):
                ui.errors.Error(
                    testset,
                    'Only domjudge_judge_runner is supported.')
                yield False

            validator_dir = os.path.join(
                pack_files_dir, 'output_validators',
                os.path.splitext(judge.src_name)[0])
            files.MakeDir(validator_dir)
            ui.console.PrintAction(
                'PACK',
                testset,
                'output validator files',
                progress=True)
            files.CopyFile(
                os.path.join(testset.src_dir, judge.src_name),
                validator_dir)
            for f in judge.dependency:
                files.CopyFile(
                    os.path.join(testset.project.library_dir, f),
                    validator_dir)

            # Generate problem.yaml
            # TODO: add more data to problem.yaml?
            yaml_file = os.path.join(pack_files_dir, 'problem.yaml')
            with open(yaml_file, 'w') as f:
                f.write('validation: custom\n')

        if (testset.problem.domjudge_config_defined and
                testset.problem.domjudge_problem_file):
            dest_filename = 'problem.pdf'
            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (testset.problem.domjudge_problem_file,
                                  dest_filename),
                    progress=True)
                files.CopyFile(
                    os.path.join(testset.problem.base_dir,
                                 testset.problem.domjudge_problem_file),
                    os.path.join(pack_files_dir, dest_filename))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        # Create a zip file
        try:
            shutil.make_archive(
                os.path.join(testset.domjudge_pack_dir, testset.problem.id),
                'zip',
                root_dir=pack_files_dir)
        except Exception:
            ui.errors.Exception(testset)
            yield False

        ui.console.PrintAction(
            'PACK', testset, f'Created {testset.problem.id}.zip')

        yield True


class DOMJudgeUploader(plus_commands.UploaderBase):
    @taskgraph.task_method
    def Upload(self, ui, problem, dryrun):
        if not problem.project.domjudge_config_defined:
            ui.errors.Error(
                problem, 'domjudge_config() is not defined in PROJECT.')
            yield False

        base_api_url = problem.project.domjudge_url + 'api/v4/'
        auth = requests.auth.HTTPBasicAuth(
            problem.project.domjudge_username,
            problem.project.domjudge_password)
        contest_id = problem.project.domjudge_contest_id

        res = requests.get(
            base_api_url + 'contests/%d/problems' % contest_id,
            auth=auth)
        if res.status_code != 200:
            ui.errors.Error(
                problem, 'Getting problems failed: %s' % res.reason)
            yield False

        possible_problems = [
            p for p in res.json() if p['externalid'] == problem.name]
        new_problem = len(possible_problems) == 0

        data = {}
        if not new_problem:
            data['problem'] = possible_problems[0]['id']
            data['delete_old_data'] = True
        packed_file = os.path.join(
            problem.testsets[0].domjudge_pack_dir, problem.id + '.zip')
        ui.console.PrintAction(
            'UPLOAD', problem, packed_file, progress=True)
        with open(packed_file, 'rb') as f:
            request_url = base_api_url + 'contests/%d/problems' % contest_id
            if not dryrun:
                res = requests.post(
                    request_url,
                    data=data,
                    files={'zip': f},
                    auth=auth)
                if res.status_code != 200:
                    ui.errors.Error(
                        problem, 'Getting problems failed: %s' % res.reason)
                    yield False
            else:
                ui.console.PrintWarning('Dry-run mode')
                ui.console.PrintWarning(
                    f'POST {request_url} with data={data}, zip={packed_file}')

        ui.console.PrintAction(
            'UPLOAD', problem, str(problem.id))
        yield True


class DOMJudgeSubmitter(plus_commands.SubmitterBase):
    _LANGUAGE_MAP = {
        'c': 'c',
        'cxx': 'cpp',
        'java': 'java',
        'kotlin': 'kotlin',
        'script': 'python3',  # assuming script = python
    }

    @taskgraph.task_method
    def Submit(self, ui, solution):
        if not solution.project.domjudge_config_defined:
            ui.errors.Error(
                solution, 'domjudge_config() is not defined in PROJECT.')
            yield False

        base_api_url = solution.project.domjudge_url + 'api/v4/'
        auth = requests.auth.HTTPBasicAuth(
            solution.project.domjudge_username,
            solution.project.domjudge_password)
        contest_id = solution.project.domjudge_contest_id

        # Get the problem id from problems list.
        res = requests.get(
            base_api_url + 'contests/%d/problems' % contest_id,
            auth=auth)
        if res.status_code != 200:
            ui.errors.Error(
                solution, 'Getting problems failed: %s' % res.reason)
            yield False

        possible_problems = [
            p for p in res.json() if p['externalid'] == solution.problem.name]
        if len(possible_problems) != 1:
            ui.errors.Error(solution, 'Problem does not exist.')
            yield False
        problem_id = possible_problems[0]['id']

        lang_name = self._LANGUAGE_MAP[solution.code.PREFIX]

        ui.console.PrintAction(
            'SUBMIT',
            solution,
            str({'problem_id': problem_id, 'language': lang_name}),
            progress=True)

        source_code_file = os.path.join(
            solution.src_dir, solution.code.src_name)
        with open(source_code_file, 'rb') as f:
            res = requests.post(
                base_api_url + 'contests/%d/submissions' % contest_id,
                data={'problem': problem_id, 'language': lang_name},
                files={'code': f},
                auth=auth)
        if res.status_code != 200:
            ui.errors.Error(solution, 'Submission failed: %s' % res.reason)
            yield False

        submission_id = res.json()['id']

        ui.console.PrintAction(
            'SUBMIT', solution, 'submitted: submission_id=%s' % submission_id,
            progress=True)

        # Poll until judge completes.
        while True:
            res = requests.get(
                base_api_url + 'contests/%d/judgements' % contest_id,
                params={'submission_id': submission_id},
                auth=auth)
            if res.status_code != 200:
                ui.errors.Error(
                    solution, 'Getting judgements failed: %s' % res.reason)
                yield False
            verdict = res.json()[0]['judgement_type_id']
            if verdict:
                break
            time.sleep(3.0)

        ui.console.PrintAction(
            'SUBMIT', solution, '%s (s%s)' % (verdict, submission_id))
        if solution.IsCorrect() is not (verdict == 'AC'):
            ui.errors.Warning(
                solution, 'Expected %s, but got %s' %
                ('pass' if solution.IsCorrect() else 'fail', verdict))

        yield True


targets.registry.Override('Project', Project)
targets.registry.Override('Problem', Problem)
targets.registry.Override('Testset', Testset)

flexible_judge.judge_runner_registry.Add(DOMJudgeJudgeRunner)
flexible_judge.reactive_runner_registry.Add(DOMJudgeReactiveRunner)

plus_commands.packer_registry.Add(DOMJudgePacker)
plus_commands.uploader_registry.Add(DOMJudgeUploader)
plus_commands.submitter_registry.Add(DOMJudgeSubmitter)
