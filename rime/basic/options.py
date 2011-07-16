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
commands.RegisterCommand(None, None, consts.GLOBAL_HELP)

commands.RegisterOption(
  None, 'h', 'help', 'help', bool, False, None,
  'Show this help.')

commands.RegisterOption(
  None, 'j', 'jobs', 'parallelism', int, 0, 'n',
  'Run multiple jobs in parallel.')

commands.RegisterOption(
  None, 'd', 'debug', 'debug', bool, False, None,
  'Turn on debugging.')

commands.RegisterOption(
  None, 'C', 'cache_tests', 'cache_tests', bool, False, None,
  'Cache test results.')

commands.RegisterOption(
  None, 'p', 'precise', 'precise', bool, False, None,
  'Do not run timing tasks concurrently.')

commands.RegisterOption(
  None, 'k', 'keep_going', 'keep_going', bool, False, None,
  'Do not skip tests on failures.')
