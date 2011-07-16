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

import glob
import os
import os.path

from rime.util import files


def LoadModule(module_fullname):
  module_name = module_fullname.split('.')[-1]
  package_name = '.'.join(module_fullname.split('.')[:-1])
  package = __import__(package_name, globals(), locals(), [module_name])
  return hasattr(package, module_name)

def LoadPackage(package_name):
  assert package_name
  package_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                             *package_name.split('.'))
  for filename in files.ListDir(package_dir):
    if (os.path.isdir(os.path.join(package_dir, filename)) and
        os.path.isfile(os.path.join(package_dir, filename, '__init__.py'))):
      LoadPackage('%s.%s' % (package_name, filename))
    elif filename.endswith('.py'):
      module_name = os.path.splitext(filename)[0]
      if module_name != '__init__':
        LoadModule('%s.%s' % (package_name, module_name))
