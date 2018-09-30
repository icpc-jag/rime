#!/usr/bin/python

import sys

from rime.util import files
from rime.util import struct


# Escape sequences.
_COLOR_ESCAPE_SEQUENCES = {
    'BOLD': '\x1b[1m',
    'RED': '\x1b[31m',
    'GREEN': '\x1b[32m',
    'YELLOW': '\x1b[33m',
    'BLUE': '\x1b[34m',
    'MAGENTA': '\x1b[35m',
    'CYAN': '\x1b[36m',
    'WHITE': '\x1b[37m',
    'NORMAL': '\x1b[0m',
}
_CONTROL_ESCAPE_SEQUENCES = {
    'UP': '\x1b[1A',
    'KILL': '\x1b[K',
}


class ConsoleBase(object):
    """Base of Console classes."""

    def __init__(self, out, caps):
        self.out = out
        self.caps = caps
        self.quiet = False
        # Whether the last print is marked "progress".
        self._last_progress = False
        for name, value in _COLOR_ESCAPE_SEQUENCES.items():
            setattr(self, name, (self.caps.color and value or ''))
        for name, value in _CONTROL_ESCAPE_SEQUENCES.items():
            setattr(self, name, (self.caps.overwrite and value or ''))

    # TODO(mizuno): Move to constructor.
    def set_quiet(self):
        self.quiet = True

    def Print(self, *args, **kwargs):
        """Print one line.

        Each argument is either ordinal string or control code.
        """
        progress = bool(kwargs.get('progress'))

        if self.quiet and progress:
            return

        msg = ''.join(args)
        if self._last_progress and self.caps.overwrite:
            self.out.write(self.UP + '\r' + msg + self.KILL + '\n')
        else:
            self.out.write(msg + '\n')
        self._last_progress = progress

    def PrintAction(self, action, obj, *args, **kwargs):
        """Utility function to print actions."""
        real_args = [self.GREEN, '[' + action.center(10) + ']', self.NORMAL]
        if obj:
            real_args += [' ', obj.fullname]
        if args:
            if obj:
                real_args += [':']
            real_args += [' '] + list(args)
        self.Print(*real_args, **kwargs)

    def PrintError(self, msg):
        """Utility function to print errors."""
        self.Print(self.RED, 'ERROR:', self.NORMAL, ' ', msg)

    def PrintWarning(self, msg):
        """Utility function to print warnings."""
        self.Print(self.YELLOW, 'WARNING:', self.NORMAL, ' ', msg)

    def PrintLog(self, log):
        """Print bare messages.

        Used to print logs such as compiler's output.
        """
        if log is None:
            return
        for line in log.splitlines():
            self.Print(line)


class TtyConsole(ConsoleBase):
    """Console output to tty."""

    def __init__(self, out):
        super(TtyConsole, self).__init__(out, self._GetCaps())

    @classmethod
    def _GetCaps(cls):
        caps = struct.Struct()
        caps.overwrite = False
        caps.color = False
        if sys.stdout.isatty():
            try:
                import curses
                curses.setupterm()
                caps.overwrite = bool(curses.tigetstr('cuu1'))
                caps.color = bool(curses.tigetstr('setaf'))
            except Exception:
                pass
        return caps


class NullConsole(ConsoleBase):
    """Null console output."""

    def __init__(self):
        null_caps = struct.Struct(color=False, overwrite=False)
        super(NullConsole, self).__init__(files.OpenNull(), null_caps)
