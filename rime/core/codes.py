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

import os.path

from rime.util import class_registry


# Registered code types.  An entry is (prefix, extension, class).
_CODE_TYPES = []


class RunResult(object):
  """Result of a single run.

  Note that this is not judgement result but just execution status.
  """

  OK = 'OK'
  NG = 'Exited Abnormally'
  RE = 'Runtime Error'
  TLE = 'Time Limit Exceeded'

  def __init__(self, status, time):
    self.status = status
    self.time = time


class Code(object):
  """Interface of program codes.

  Supports operations such as compile, run, clean.
  """

  # Set to True if the deriving class does not require compilation
  # (e.g. script language).
  QUIET_COMPILE = False

  def __init__(self, src_name, src_dir, out_dir):
    self.src_name = src_name
    self.src_dir = src_dir
    self.out_dir = out_dir

  def Compile(self):
    raise NotImplementedError()

  def Run(self, args, cwd, input, output, timeout, precise, redirect_error=False):
    raise NotImplementedError()

  def Clean(self):
    raise NotImplementedError()


class RegistrationError(Exception):
  pass


def Register(name, extensions, code_class):
  """Registers a code class."""
  for entry_name, entry_extensions, _ in _CODE_TYPES:
    if entry_name == name:
      raise RegistrationError('Duplicate code class name: %s' % name)
    dup_extensions = list(set(entry_extensions) & set(extensions))
    if dup_extensions:
      raise RegistrationError('Duplicate code class extension: %s' %
                              dup_extensions)
  _CODE_TYPES.append((name, extensions, code_class))


def ExportDictionary(name_fmt, codeset, src_dir, out_dir):
  """Exports a dictionary used for configs."""
  export = {}
  for name, _, code_class in _CODE_TYPES:
    def Closure(code_class):
      def Registerer(src, *args, **kwargs):
        codeset.append(
          code_class(src_name=src, src_dir=src_dir, out_dir=out_dir,
                     *args, **kwargs))
      export[name_fmt % name] = Registerer
    Closure(code_class)
  return export


def CreateCodeByExtension(src_name, src_dir, out_dir, *args, **kwargs):
  src_ext = os.path.splitext(src_name)[1][1:]
  for _, code_extensions, code_class in _CODE_TYPES:
    if src_ext in code_extensions:
      return code_class(src_name, src_dir, out_dir, *args, **kwargs)
  return None
