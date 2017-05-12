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

import optparse
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
  def Run(self, args, cwd, input, output, timeout, precise, redirect_error=False):
    """Run the code and return RunResult."""
    try:
      result = yield self._ExecForRun(
        args=tuple(list(self.run_args)+list(args)), cwd=cwd,
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
          stdin=files.OpenNull(), stdout=outfile, stderr=subprocess.STDOUT))

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
            stdin=infile, stdout=outfile, stderr=errfile, timeout=timeout,
            precise=precise))

  @taskgraph.task_method
  def _ExecInternal(self, args, cwd, stdin, stdout, stderr,
                    timeout=None, precise=False):
    task = taskgraph.ExternalProcessTask(
      args, cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout,
      exclusive=precise)
    proc = yield task
    code = proc.returncode
    # Retry if TLE.
    if not precise and code == -(signal.SIGXCPU):
      self._ResetIO(stdin, stdout, stderr)
      task = taskgraph.ExternalProcessTask(
        args, cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout,
        exclusive=True)
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
    super(CCode, self).__init__(
      src_name=src_name, src_dir=src_dir, out_dir=out_dir,
      compile_args=(['gcc',
                     '-o', os.path.join(out_dir, exe_name),
                     src_name] + list(flags)),
      run_args=[os.path.join(out_dir, exe_name)])


class CXXCode(CodeBase):
  PREFIX = 'cxx'
  EXTENSIONS = ['cc', 'cxx']

  def __init__(self, src_name, src_dir, out_dir, flags=[]):
    exe_name = os.path.splitext(src_name)[0] + consts.EXE_EXT
    super(CXXCode, self).__init__(
      src_name=src_name, src_dir=src_dir, out_dir=out_dir,
      compile_args=(['g++',
                     '-o', os.path.join(out_dir, exe_name),
                     src_name] + list(flags)),
      run_args=[os.path.join(out_dir, exe_name)])


class JavaCode(CodeBase):
  PREFIX = 'java'
  EXTENSIONS = ['java']

  def __init__(self, src_name, src_dir, out_dir,
               compile_flags=[], run_flags=[],
               encoding='UTF-8', mainclass='Main'):
    super(JavaCode, self).__init__(
      src_name=src_name, src_dir=src_dir, out_dir=out_dir,
      compile_args=(['javac', '-encoding', encoding,
                     '-d', files.ConvPath(out_dir)] +
                    compile_flags + [src_name]),
      run_args=(['java', '-Dline.separator=\n',
                 '-cp', files.ConvPath(out_dir)] +
                run_flags + [mainclass]))


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
      yield codes.RunResult('Interpreter not found: %s' % interpreter, None)
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
  def Run(self, args, cwd, input, output, timeout, precise, redirect_error=False):
    # files are specified in same way as testlib.h.
    # "./judge.exe <in_file> <out_file> <diff_file>"
    run_args = ('diff', '-u', args[2], args[1])
    with open(input, 'r') as infile:
      with open(output, 'w') as outfile:
        if redirect_error:
          errfile = subprocess.STDOUT
        else:
          errfile = files.OpenNull()
        task = taskgraph.ExternalProcessTask(
          run_args, cwd=cwd, stdin=infile, stdout=outfile, stderr=errfile,
          timeout=timeout)
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
codes.registry.Add(JavaCode)
codes.registry.Add(ScriptCode)
