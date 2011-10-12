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

from rime.basic import consts


class TestVerdict(object):

  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg


class TestCase(object):

  def __init__(self, testset, infile, difffile=None):
    self.testset = testset
    self.infile = infile
    if difffile is None:
      self.difffile = os.path.splitext(infile)[0] + consts.DIFF_EXT
    else:
      self.difffile = difffile

  @property
  def timeout(self):
    return self.testset.problem.timeout


class TestCaseResult(object):
  """Testcase result."""

  NA = TestVerdict('-')
  AC = TestVerdict('Accepted')
  WA = TestVerdict('Wrong Answer')
  TLE = TestVerdict('Time Limit Exceeded')
  RE = TestVerdict('Runtime Error')
  ERR = TestVerdict('System Error')

  def __init__(self, solution, testcase, verdict, time, cached):
    self.solution = solution
    self.testcase = testcase
    self.verdict = verdict
    self.time = time
    self.cached = cached


class TestsetResult(object):
  """Testset result.

  This includes sub-results for each testcase.
  """

  def __init__(self, testset, solution, testcases):
    """Construct with empty results."""
    self.testset = testset
    self.problem = testset.problem
    self.solution = solution
    self.testcases = testcases
    self.results = dict(
      [(testcase,
        TestCaseResult(solution, testcase, TestCaseResult.NA,
                       time=None, cached=False))
       for testcase in testcases])
    assert len(self.results) == len(testcases)
    self.finalized = False

  def IsFinalized(self):
    return self.finalized

  def Finalize(self, expected, detail, notable_testcase=None,
               allow_override=False):
    if self.finalized and not allow_override:
      return
    self.expected = expected
    self.detail = detail
    self.notable_testcase = notable_testcase
    self.finalized = True

  def IsCached(self):
    return any((c.cached for c in self.results.values()))

  def IsAccepted(self):
    return all((c.verdict == TestCaseResult.AC for c in self.results.values()))

  def IsTimingValid(self, ui):
    """Checks if timing stats are valid."""
    return ((ui.options.precise or ui.options.parallelism <= 1) and
            self.results and
            all((c.verdict == TestCaseResult.AC
                 for c in self.results.values())))

  def GetTimeStats(self, ui):
    """Get time statistics."""
    # TODO(nya): Concat support
    if not self.IsTimingValid(ui):
      return 'max *.**s, acc *.**s'
    return 'max %.2fs, acc %.2fs' % (self.GetMaxTime(), self.GetTotalTime())

  def GetMaxTime(self):
    """Get maximum time.

    All case should be accepted.
    """
    return max([c.time for k, c in self.results.items()])

  def GetTotalTime(self):
    """Get total time.

    All case should be accepted.
    """
    return sum([c.time for k, c in self.results.items()])
