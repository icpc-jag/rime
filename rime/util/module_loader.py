#!/usr/bin/python

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
                os.path.isfile(os.path.join(
                    package_dir, filename, '__init__.py'))):
            LoadPackage('%s.%s' % (package_name, filename))
        elif filename.endswith('.py'):
            module_name = os.path.splitext(filename)[0]
            if module_name != '__init__':
                LoadModule('%s.%s' % (package_name, module_name))
