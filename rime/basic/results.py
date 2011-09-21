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

from rime.basic import consts


class SingleCaseResult(object):
  """Test result of a single solution versus a single test case."""

  def __init__(self, verdict, time):
    # Pre-defined list of verdicts are listed in TestResult.
    self.verdict = verdict
    self.time = time


class TestResult(object):
  """Test result of a single solution.

  This includes sub-results for each test case.
  """

  # Note: verdict can be set different from any of these;
  # in that case, you should treat it as System Error.
  NA = '-'
  AC = 'Accepted'
  WA = 'Wrong Answer'
  TLE = 'Time Limit Exceeded'
  RE = 'Runtime Error'
  ERR = 'System Error'

  def __init__(self, problem, solution, files):
    """Construct with empty results."""
    self.problem = problem
    self.solution = solution
    self.files = files[:]
    self.cases = dict(
      [(f, SingleCaseResult(TestResult.NA, None))
       for f in files])
    self.good = None
    self.passed = None
    self.detail = None
    self.ruling_file = None
    self.cached = False

  def IsTimeStatsAvailable(self, ui):
    """Checks if time statistics are available."""
    return ((ui.options.precise or ui.options.parallelism == 1) and
            self.files and
            all([c.verdict == TestResult.AC for c in self.cases.values()]))

  def GetTimeStats(self):
    """Get time statistics."""
    # TODO(nya): Concat support
    #if (consts.CONCAT_INFILE in self.cases and
    #    self.cases[consts.CONCAT_INFILE].time is not None):
    #  return '(%.2f/%.2f/%.2f)' % (self.GetMaxTime(), self.GetTotalTime(),
    #                               self.cases[consts.CONCAT_INFILE].time)
    return '(%.2f/%.2f)' % (self.GetMaxTime(), self.GetTotalTime())

  def GetMaxTime(self):
    """Get maximum time.

    All case should be accepted.
    """
    return max([c.time for k, c in self.cases.items() if not k.startswith('.')])

  def GetTotalTime(self):
    """Get total time.

    All case should be accepted.
    """
    return sum([c.time for k, c in self.cases.items() if not k.startswith('.')])
