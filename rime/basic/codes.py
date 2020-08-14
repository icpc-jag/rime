#!/usr/bin/python

import optparse
import os
import os.path
import signal
import subprocess

from rime.basic import consts
from rime.core import codes
from rime.core import taskgraph
from rime.util import files


class CodeBase(codes.Code):
    """Base class of program codes with various common methods."""

    def __init__(self, src_name, src_dir, out_dir, compile_args, run_args):
        super(CodeBase, self).__init__(src_name, src_dir, out_dir)
        self.log_name = os.path.splitext(src_name)[0] + consts.LOG_EXT
        self.compile_args = tuple(compile_args)
        self.run_args = tuple(run_args)

    @taskgraph.task_method
    def Compile(self):
        """Compile the code and return RunResult."""
        try:
            if not self.compile_args:
                result = codes.RunResult(codes.RunResult.OK, None)
            else:
                result = yield self._ExecForCompile(args=self.compile_args)
        except Exception as e:
            result = codes.RunResult('On compiling: %s' % e, None)
        yield result

    @taskgraph.task_method
    def Run(self, args, cwd, input, output, timeout, precise,
            redirect_error=False):
        """Run the code and return RunResult."""
        try:
            result = yield self._ExecForRun(
                args=tuple(list(self.run_args) + list(args)), cwd=cwd,
                input=input, output=output, timeout=timeout, precise=precise,
                redirect_error=redirect_error)
        except Exception as e:
            result = codes.RunResult('On execution: %s' % e, None)
        yield result

    @taskgraph.task_method
    def Clean(self):
        """Cleans the output directory.

        Returns an exception object on error.
        """
        try:
            files.RemoveTree(self.out_dir)
        except Exception as e:
            yield e
        else:
            yield None

    def ReadCompileLog(self):
        return files.ReadFile(os.path.join(self.out_dir, self.log_name))

    @taskgraph.task_method
    def _ExecForCompile(self, args):
        with open(os.path.join(self.out_dir, self.log_name), 'w') as outfile:
            yield (yield self._ExecInternal(
                args=args, cwd=self.src_dir,
                stdin=files.OpenNull(), stdout=outfile,
                stderr=subprocess.STDOUT))

    @taskgraph.task_method
    def _ExecForRun(self, args, cwd, input, output, timeout, precise,
                    redirect_error=False):
        with open(input, 'r') as infile:
            with open(output, 'w') as outfile:
                if redirect_error:
                    errfile = subprocess.STDOUT
                else:
                    errfile = files.OpenNull()
                yield (yield self._ExecInternal(
                    args=args, cwd=cwd,
                    stdin=infile, stdout=outfile, stderr=errfile,
                    timeout=timeout, precise=precise))

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
                timeout=timeout, exclusive=True)
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

    def _ResetIO(self, *args):
        for f in args:
            if f is None:
                continue
            try:
                f.seek(0)
                f.truncate()
            except IOError:
                pass


class CCode(CodeBase):
    PREFIX = 'c'
    EXTENSIONS = ['c']

    def __init__(self, src_name, src_dir, out_dir, flags=['-lm']):
        exe_name = os.path.splitext(src_name)[0] + consts.EXE_EXT
        cc = os.getenv('CC', 'gcc')
        super(CCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=([cc,
                           '-o', os.path.join(out_dir, exe_name),
                           src_name] + list(flags)),
            run_args=[os.path.join(out_dir, exe_name)])


class CXXCode(CodeBase):
    PREFIX = 'cxx'
    EXTENSIONS = ['cc', 'cxx']

    def __init__(self, src_name, src_dir, out_dir, flags=[]):
        exe_name = os.path.splitext(src_name)[0] + consts.EXE_EXT
        cxx = os.getenv('CXX', 'g++')
        super(CXXCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=([cxx,
                           '-o', os.path.join(out_dir, exe_name),
                           src_name] + list(flags)),
            run_args=[os.path.join(out_dir, exe_name)])


class KotlinCode(CodeBase):
    PREFIX = 'kotlin'
    EXTENSIONS = ['kt']

    def __init__(self, src_name, src_dir, out_dir,
                 compile_flags=[], run_flags=[]):
        kotlinc = 'kotlinc'
        kotlin = 'kotlin'
        mainclass = os.path.splitext(src_name)[0].capitalize() + 'Kt'
        super(KotlinCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=([kotlinc, '-d', files.ConvPath(out_dir)] +
                          compile_flags + [src_name]),
            run_args=([kotlin, '-Dline.separator=\n',
                       '-cp', files.ConvPath(out_dir)] +
                      run_flags + [mainclass]))


class JavaCode(CodeBase):
    PREFIX = 'java'
    EXTENSIONS = ['java']

    def __init__(self, src_name, src_dir, out_dir,
                 compile_flags=[], run_flags=[],
                 encoding='UTF-8', mainclass='Main'):
        java_home = os.getenv('JAVA_HOME')
        if java_home is not None:
            java = os.path.join(java_home, 'bin/java')
            javac = os.path.join(java_home, 'bin/javac')
        else:
            java = 'java'
            javac = 'javac'
        super(JavaCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=([javac, '-encoding', encoding,
                           '-d', files.ConvPath(out_dir)] +
                          compile_flags + [src_name]),
            run_args=([java, '-Dline.separator=\n',
                       '-cp', files.ConvPath(out_dir)] +
                      run_flags + [mainclass]))


class RustCode(CodeBase):
    PREFIX = 'rust'
    EXTENSIONS = ['rs']

    def __init__(self, src_name, src_dir, out_dir, flags=[]):
        exe_name = os.path.splitext(src_name)[0] + consts.EXE_EXT
        rustc = 'rustc'
        super(RustCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=([rustc,
                           '-o', os.path.join(out_dir, exe_name),
                           src_name] + list(flags)),
            run_args=[os.path.join(out_dir, exe_name)])


class GoCode(CodeBase):
    PREFIX = 'go'
    EXTENSIONS = ['go']

    def __init__(self, src_name, src_dir, out_dir, flags=[]):
        exe_name = os.path.splitext(src_name)[0] + consts.EXE_EXT
        goc = 'go'
        super(GoCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=([goc, 'build',
                           '-o', os.path.join(out_dir, exe_name)] +
                          flags + [src_name]),
            run_args=[os.path.join(out_dir, exe_name)])


class ScriptCode(CodeBase):
    QUIET_COMPILE = True
    PREFIX = 'script'
    EXTENSIONS = ['sh', 'pl', 'py', 'rb']

    def __init__(self, src_name, src_dir, out_dir, run_flags=[]):
        super(ScriptCode, self).__init__(
            src_name=src_name, src_dir=src_dir, out_dir=out_dir,
            compile_args=[],
            run_args=['false', os.path.join(src_dir, src_name)] + run_flags)
        # Replace the executable with the shebang line
        run_args = list(self.run_args)
        try:
            run_args[0] = self._ReadAndParseShebangLine()
        except IOError:
            pass
        self.run_args = tuple(run_args)

    @taskgraph.task_method
    def Compile(self, *args, **kwargs):
        """Fail if the script is missing a shebang line."""
        try:
            interpreter = self._ReadAndParseShebangLine()
        except IOError:
            yield codes.RunResult('File not found', None)
        if not interpreter:
            yield codes.RunResult('Script missing a shebang line', None)
        if not os.path.exists(interpreter):
            yield codes.RunResult('Interpreter not found: %s' % interpreter,
                                  None)
        yield (yield super(ScriptCode, self).Compile(*args, **kwargs))

    def _ReadAndParseShebangLine(self):
        with open(os.path.join(self.src_dir, self.src_name)) as f:
            shebang_line = f.readline()
        if not shebang_line.startswith('#!'):
            return None
        return shebang_line[2:].strip()


class InternalDiffCode(CodeBase):
    QUIET_COMPILE = True

    def __init__(self):
        super(InternalDiffCode, self).__init__(
            src_name='diff',
            src_dir='',
            out_dir='',
            compile_args=[],
            run_args=[])

    @taskgraph.task_method
    def Run(self, args, cwd, input, output, timeout, precise,
            redirect_error=False):
        parser = optparse.OptionParser()
        parser.add_option('-i', '--infile', dest='infile')
        parser.add_option('-d', '--difffile', dest='difffile')
        parser.add_option('-o', '--outfile', dest='outfile')
        (options, pos_args) = parser.parse_args([''] + list(args))
        run_args = ('diff', '-u', options.difffile, options.outfile)
        with open(input, 'r') as infile:
            with open(output, 'w') as outfile:
                if redirect_error:
                    errfile = subprocess.STDOUT
                else:
                    errfile = files.OpenNull()
                task = taskgraph.ExternalProcessTask(
                    run_args, cwd=cwd, stdin=infile, stdout=outfile,
                    stderr=errfile, timeout=timeout)
                try:
                    proc = yield task
                except OSError:
                    yield codes.RunResult(codes.RunResult.RE, None)
                ret = proc.returncode
                if ret == 0:
                    yield codes.RunResult(codes.RunResult.OK, task.time)
                if ret > 0:
                    yield codes.RunResult(codes.RunResult.NG, None)
                yield codes.RunResult(codes.RunResult.RE, None)

    @taskgraph.task_method
    def Clean(self):
        yield True


codes.registry.Add(CCode)
codes.registry.Add(CXXCode)
codes.registry.Add(KotlinCode)
codes.registry.Add(JavaCode)
codes.registry.Add(RustCode)
codes.registry.Add(GoCode)
codes.registry.Add(ScriptCode)
