# Copyright (c) 2017 Rime Project.
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

import sys

import setuptools


if sys.version_info[0] != 2:
  print('Rime supports Python 2 only at this moment.')
  print('Please use:')
  print('    python2 -m pip install git+https://github.com/icpc-jag/rime')
  sys.exit(1)

setuptools.setup(
    name='rime',
    version='2.0.dev1',
    scripts=['bin/rime', 'bin/rime_init'],
    packages=['rime', 'rime.basic', 'rime.basic.targets', 'rime.basic.util',
              'rime.core', 'rime.plugins', 'rime.plugins.judge_system',
              'rime.plugins.plus', 'rime.util'],
    package_dir={'rime': 'rime'},
    install_requires=['six'],
    test_suite='nose.collector',
    tests_require=['nose', 'mox'],
)
