#!/usr/bin/python
#
# Copyright (c) 2015 Rime Project.
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
import os
import os.path
import subprocess
import cookielib
import re
import sys
import time
import urllib
import urllib2

import rime.basic.targets.testset   # target dependency
from rime.basic import consts
from rime.basic import commands as basic_commands
from rime.basic import codes as basic_codes
from rime.core import commands
from rime.core import targets
from rime.core import taskgraph
from rime.util import files
from rime.plugins.plus import commands as plus_commands

class Testset(targets.registry.Testset):
  def __init__(self, *args, **kwargs):
    super(Testset, self).__init__(*args, **kwargs)
    self.mjudge_pack_dir = os.path.join(self.problem.out_dir, 'mjudge')

class MJudgePacker(plus_commands.PackerBase):
  @taskgraph.task_method
  def Pack(self, ui, testset):
    testcases = testset.ListTestCases()
    try:
      files.RemoveTree(testset.mjudge_pack_dir)
      files.MakeDir(testset.mjudge_pack_dir)
    except:
      ui.errors.Exception(testset)
      yield False
    for (i, testcase) in enumerate(testcases):
      basename = os.path.splitext(testcase.infile)[0]
      difffile = basename + consts.DIFF_EXT
      packed_infile = str(i+1) + consts.IN_EXT
      packed_difffile = str(i+1) + consts.DIFF_EXT
      try:
        ui.console.PrintAction(
          'PACK',
          testset,
          '%s -> %s' % (os.path.basename(testcase.infile), packed_infile),
          progress=True)
        files.CopyFile(os.path.join(testset.out_dir, testcase.infile),
                       os.path.join(testset.mjudge_pack_dir, packed_infile))
        ui.console.PrintAction(
          'PACK',
          testset,
          '%s -> %s' % (os.path.basename(difffile), packed_difffile),
          progress=True)
        files.CopyFile(os.path.join(testset.out_dir, difffile),
                       os.path.join(testset.mjudge_pack_dir, packed_difffile))
      except:
        ui.errors.Exception(testset)
        yield False
    yield True

targets.registry.Override('Testset',  Testset)

plus_commands.packer_registry.Add(MJudgePacker)
