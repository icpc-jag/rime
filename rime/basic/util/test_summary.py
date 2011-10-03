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

def PrintTestSummary(results, ui):
  if len(results) == 0:
    return
  ui.console.Print()
  ui.console.Print(ui.console.BOLD, 'Test Summary:', ui.console.NORMAL)
  solution_name_width = max(
    map(lambda t: len(t.solution.name), results))
  last_problem = None
  for result in sorted(results, CompareTestResultForListing):
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
      result.solution.IsCorrect() and ui.console.GREEN or ui.console.YELLOW,
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
  if not (ui.options.precise or ui.options.parallelism <= 1):
    ui.console.Print()
    ui.console.Print('Note: Timings are not displayed when '
                     'parallel testing is enabled.')
    ui.console.Print('      To show them, try -p (--precise).')


def CompareTestResultForListing(a, b):
  """Compare two TestResult for display-ordering."""
  if a.problem.name != b.problem.name:
    return cmp(a.problem.name, b.problem.name)
  reference_solution = a.problem.reference_solution
  if a.solution is reference_solution:
    return -1
  if b.solution is reference_solution:
    return +1
  if a.solution.IsCorrect() != b.solution.IsCorrect():
    return -cmp(a.solution.IsCorrect(), b.solution.IsCorrect())
  return cmp(a.solution.name, b.solution.name)
