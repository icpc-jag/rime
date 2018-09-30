#!/usr/bin/python

import os
import os.path
import sys

from rime.util import class_registry
from rime.util import files
from rime.util import module_loader


class TargetBase(object):
    """Base class of all target types."""

    # Config filename of this target.  Every subclass should override this.
    CONFIG_FILENAME = None

    def __init__(self, name, base_dir, parent):
        """Constructs a new unconfigured target."""
        self.name = name
        self.base_dir = base_dir
        self.parent = parent

        # Set full name.
        # Full name is normally path-like string separated with "/".
        if name is None:
            self.name = '<root>'
            self.fullname = None
        elif parent is None or parent.fullname is None:
            self.fullname = name
        else:
            self.fullname = parent.fullname + '/' + name

        # Locate config file.
        self.config_file = os.path.join(base_dir, self.CONFIG_FILENAME)

        self.exports = {}
        self.configs = {}

        self._loaded = False

    def Export(self, method, name=None):
        """Exports a method to config modules."""
        if not name:
            name = method.__name__
        assert name not in self.exports, '%s already in exports!'
        self.exports[name] = method

    def Load(self, ui):
        """Loads configurations and do setups.

        Raises:
          ConfigurationError: configuration is missing or incorrect.
        """
        assert not self._loaded, 'TargetBase.Load() called twice!'
        self._loaded = True

        # Evaluate config.
        try:
            script = files.ReadFile(self.config_file)
        except IOError:
            raise ConfigurationError('cannot read file: %s' % self.config_file)
        try:
            code = compile(script, self.config_file, 'exec')
            self.PreLoad(ui)
            exec(code, self.exports, self.configs)
            self.PostLoad(ui)
        except ReloadConfiguration:
            raise  # Passthru
        except Exception as e:
            # TODO(nya): print pretty file/lineno for debug
            raise ConfigurationError(e)

    def PreLoad(self, ui):
        """Called just before evaluation of configs.

        Subclasses should setup exported symbols by self.exports.
        """
        pass

    def PostLoad(self, ui):
        """Called just after evaluation of configs.

        Subclasses can do post-processing of configs here.
        """
        pass

    def FindByBaseDir(self, base_dir):
        """Search whole subtree and return the object with matching base_dir.

        Subclasses may want to override this method for recursive search.
        """
        if self.base_dir == base_dir:
            return self
        return None

    @classmethod
    def CanLoadFrom(self, base_dir):
        return os.path.isfile(os.path.join(base_dir, self.CONFIG_FILENAME))


class ConfigurationError(Exception):
    pass


class ReloadConfiguration(Exception):
    pass


class Project(TargetBase):
    """Project target.

    Project is the only target defined in rime.core. Here, only special methods
    which need to be cared in the core library are defined, e.g. use_plugin().
    """

    CONFIG_FILENAME = 'PROJECT'

    def PreLoad(self, ui):
        # Do not use super() here because targets.Project will be overridden.
        TargetBase.PreLoad(self, ui)

        def use_plugin(name):
            module_name = 'rime.plugins.%s' % name
            if module_name not in sys.modules:
                if not module_loader.LoadModule(module_name):
                    raise ConfigurationError(
                        'Failed to load a plugin: %s' % name)
                raise ReloadConfiguration('use_plugin(%s)' % repr(name))
        self.exports['use_plugin'] = use_plugin


registry = class_registry.ClassRegistry(TargetBase)
registry.Add(Project)
