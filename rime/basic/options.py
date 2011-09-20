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
from rime.core import commands


# Register the root command and global options.
class Default(commands.CommandBase):
  def __init__(self, parent):
    assert parent is None
    super(Default, self).__init__(None, consts.GLOBAL_HELP, parent)
    self.AddOptionEntry(commands.OptionEntry(
        'h', 'help', 'help', bool, False, None,
        'Show this help.'))
    self.AddOptionEntry(commands.OptionEntry(
        'j', 'jobs', 'parallelism', int, 0, 'n',
        'Run multiple jobs in parallel.'))
    self.AddOptionEntry(commands.OptionEntry(
        'd', 'debug', 'debug', bool, False, None,
        'Turn on debugging.'))
    self.AddOptionEntry(commands.OptionEntry(
        'C', 'cache_tests', 'cache_tests', bool, False, None,
        'Cache test results.'))
    self.AddOptionEntry(commands.OptionEntry(
        'p', 'precise', 'precise', bool, False, None,
        'Do not run timing tasks concurrently.'))
    self.AddOptionEntry(commands.OptionEntry(
        'k', 'keep_going', 'keep_going', bool, False, None,
        'Do not skip tests on failures.'))

commands.registry.Add(Default)
