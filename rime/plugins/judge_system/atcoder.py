#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import re
import time

from six.moves import http_cookiejar
from six.moves import urllib

from rime.basic import codes as basic_codes
from rime.basic import consts
import rime.basic.targets.problem
import rime.basic.targets.project
import rime.basic.targets.solution
import rime.basic.targets.testset  # NOQA
from rime.core import targets
from rime.core import taskgraph
from rime.plugins.plus import commands as plus_commands
from rime.util import files


# opener with cookiejar
cookiejar = http_cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cookiejar))


class Project(targets.registry.Project):
    def PreLoad(self, ui):
        super(Project, self).PreLoad(ui)
        self.atcoder_config_defined = False

        def _atcoder_config(upload_script, contest_url, username, password,
                            lang_ids):
            self.atcoder_config_defined = True
            self.atcoder_upload_script = upload_script
            self.atcoder_contest_url = contest_url
            self.atcoder_username = username
            self.atcoder_password = password
            self.atcoder_lang_ids = lang_ids
        self.exports['atcoder_config'] = _atcoder_config
        self.atcoder_logined = False

    @taskgraph.task_method
    def Upload(self, ui):
        script = os.path.join(self.atcoder_upload_script)
        if not os.path.exists(os.path.join(self.base_dir, script)):
            ui.errors.Error(self, script + ' is not found.')
            yield False
        yield super(Project, self).Upload(ui)

    def _Request(self, path, data=None):
        if type(data) == dict:
            data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(self.atcoder_contest_url + path, data)
        return opener.open(req)

    def _Login(self):
        if not self.atcoder_logined:
            self._Request('login',
                          {'name': self.atcoder_username,
                           'password': self.atcoder_password})
            self.atcoder_logined = True


class Problem(targets.registry.Problem):
    def PreLoad(self, ui):
        super(Problem, self).PreLoad(ui)
        self.atcoder_config_defined = False

        def _atcoder_config(task_id=None):
            self.atcoder_config_defined = True
            self.atcoder_task_id = task_id
        self.exports['atcoder_config'] = _atcoder_config

    @taskgraph.task_method
    def Submit(self, ui):
        if not self.atcoder_config_defined:
            ui.errors.Error(
                self, 'atcoder_config() is not defined in PROBLEM.')
            yield False
        if self.atcoder_task_id is None:
            ui.console.PrintAction(
                'SUBMIT', self,
                'This problem is considered to a spare. Not submitted.')
            yield True
        yield super(Problem, self).Submit(ui)


class Testset(targets.registry.Testset):
    def __init__(self, *args, **kwargs):
        super(Testset, self).__init__(*args, **kwargs)
        self.atcoder_pack_dir = os.path.join(self.problem.out_dir, 'atcoder')


class AtCoderPacker(plus_commands.PackerBase):
    @taskgraph.task_method
    def Pack(self, ui, testset):
        testcases = testset.ListTestCases()
        try:
            files.RemoveTree(testset.atcoder_pack_dir)
            files.MakeDir(testset.atcoder_pack_dir)
            files.MakeDir(os.path.join(testset.atcoder_pack_dir, 'in'))
            files.MakeDir(os.path.join(testset.atcoder_pack_dir, 'out'))
            files.MakeDir(os.path.join(testset.atcoder_pack_dir, 'etc'))
        except Exception:
            ui.errors.Exception(testset)
            yield False
        for (i, testcase) in enumerate(testcases):
            basename = os.path.splitext(testcase.infile)[0]
            difffile = basename + consts.DIFF_EXT
            packed_infile = os.path.join('in', os.path.basename(basename))
            packed_difffile = os.path.join('out', os.path.basename(basename))
            try:
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(testcase.infile),
                                  packed_infile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                               os.path.join(testset.atcoder_pack_dir,
                                            packed_infile))
                ui.console.PrintAction(
                    'PACK',
                    testset,
                    '%s -> %s' % (os.path.basename(difffile), packed_difffile),
                    progress=True)
                files.CopyFile(os.path.join(testset.out_dir, difffile),
                               os.path.join(testset.atcoder_pack_dir,
                                            packed_difffile))
            except Exception:
                ui.errors.Exception(testset)
                yield False

        # checker
        checker = testset.judges[0]
        if (len(testset.judges) == 1 and
                not isinstance(checker, basic_codes.InternalDiffCode)):
            ui.console.PrintAction(
                'PACK', testset, 'output checker files', progress=True)
            files.CopyFile(
                os.path.join(testset.src_dir, checker.src_name),
                os.path.join(testset.atcoder_pack_dir, 'etc',
                             'output_checker.cpp'))
            for f in checker.dependency:
                files.CopyFile(os.path.join(testset.project.library_dir, f),
                               os.path.join(testset.atcoder_pack_dir, 'etc',
                                            f))
        elif len(testset.judges) > 1:
            ui.errors.Error(
                testset, "Multiple output checker is not supported!")
            yield False

        # reactive
        if len(testset.reactives) == 1:
            reactive = testset.reactives[0]
            ui.console.PrintAction(
                'PACK', testset, 'reactive checker files', progress=True)
            files.CopyFile(
                os.path.join(testset.src_dir, reactive.src_name),
                os.path.join(testset.atcoder_pack_dir, 'etc', 'reactive.cpp'))
            for f in reactive.dependency:
                files.CopyFile(os.path.join(testset.project.library_dir, f),
                               os.path.join(testset.atcoder_pack_dir, 'etc',
                                            f))
            # outは使わない
            files.RemoveTree(os.path.join(testset.atcoder_pack_dir, 'out'))
        elif len(testset.judges) > 1:
            ui.errors.Error(
                testset, "Multiple reactive checker is not supported!")
            yield False

        # score.txt
        subtasks = testset.subtask_testcases
        if len(subtasks) > 0:
            score = '\n'.join([
                s.name + '(' + str(s.score) + ')' + ': ' +
                ','.join(s.input_patterns)
                for s in subtasks])
        else:
            score = 'All(100): *'
        files.WriteFile(
            score, os.path.join(testset.atcoder_pack_dir, 'etc', 'score.txt'))

        yield True


class AtCoderUploader(plus_commands.UploaderBase):
    @taskgraph.task_method
    def Upload(self, ui, problem, dryrun):
        if not problem.project.atcoder_config_defined:
            ui.errors.Error(
                problem, 'atcoder_config() is not defined in PROJECT.')
            yield False

        if not problem.atcoder_config_defined:
            ui.errors.Error(
                problem, 'atcoder_config() is not defined in PROBLEM.')
            yield False

        if problem.atcoder_task_id is None:
            ui.console.PrintAction(
                'UPLOAD', problem,
                'This problem is considered to a spare. Not uploaded.')
            yield True

        script = os.path.join(problem.project.atcoder_upload_script)
        if not os.path.exists(os.path.join(problem.project.base_dir, script)):
            ui.errors.Error(problem, script + ' is not found.')
            yield False

        stmp = files.ReadFile(script)
        if not stmp.startswith('#!/usr/bin/php'):
            ui.errors.Error(problem, script + ' is not an upload script.')
            yield False

        log = os.path.join(problem.out_dir, 'upload_log')

        if not dryrun:
            args = ('php', script, str(problem.atcoder_task_id),
                    problem.testset.atcoder_pack_dir)
        else:
            ui.console.PrintWarning('Dry-run mode')
            args = ('echo', 'php', script, str(problem.atcoder_task_id),
                    problem.testset.atcoder_pack_dir)

        ui.console.PrintAction(
            'UPLOAD', problem, ' '.join(args), progress=True)
        devnull = files.OpenNull()

        with open(log, 'a+') as logfile:
            task = taskgraph.ExternalProcessTask(
                args, cwd=problem.project.base_dir,
                stdin=devnull, stdout=logfile, stderr=logfile, exclusive=True)
            try:
                proc = yield task
            except Exception:
                ui.errors.Exception(problem)
                yield False
            ret = proc.returncode
            if ret != 0:
                ui.errors.Error(problem, 'upload failed: ret = %d' % ret)
                yield False
            ui.console.PrintAction(
                'UPLOAD', problem, str(problem.atcoder_task_id))
            yield True


class AtCoderSubmitter(plus_commands.SubmitterBase):
    @taskgraph.task_method
    def Submit(self, ui, solution):
        if not solution.project.atcoder_config_defined:
            ui.errors.Error(
                solution, 'atcoder_config() is not defined in PROJECT.')
            yield False

        solution.project._Login()

        task_id = str(solution.problem.atcoder_task_id)
        lang_id = solution.project.atcoder_lang_ids[solution.code.PREFIX]
        source_code = files.ReadFile(
            os.path.join(solution.src_dir, solution.code.src_name))

        ui.console.PrintAction(
            'SUBMIT', solution, str({'task_id': task_id, 'lang_id': lang_id}),
            progress=True)

        html = solution.project._Request('submit?task_id=%s' % task_id).read()
        pat = re.compile(r'name="__session" value="([^"]+)"')
        m = pat.search(str(html))
        session = m.group(1)
        r = solution.project._Request('submit?task_id=%s' % task_id, {
            '__session': session,
            'task_id': task_id,
            'language_id_' + task_id: lang_id,
            'source_code': source_code})
        r.read()

        results = solution.project._Request('submissions/me').read()
        submit_id = str(results).split(
            '<td><a href="/submissions/')[1].split('"')[0]

        ui.console.PrintAction(
            'SUBMIT', solution, 'submitted: ' + str(submit_id), progress=True)

        while True:
            result, progress = str(solution.project._Request(
                'submissions/' + submit_id).read()).split(
                'data-title="')[1].split('"', 1)
            if 'Judging' not in result:
                break
            time.sleep(5.0)

        if solution.IsCorrect():
            expected = ''
        else:
            expected = '(fake solution)'
        ui.console.PrintAction(
            'SUBMIT', solution, '{0} {1}'.format(result, expected))

        yield True


targets.registry.Override('Project', Project)
targets.registry.Override('Problem', Problem)
targets.registry.Override('Testset', Testset)

plus_commands.packer_registry.Add(AtCoderPacker)
plus_commands.uploader_registry.Add(AtCoderUploader)
plus_commands.submitter_registry.Add(AtCoderSubmitter)
