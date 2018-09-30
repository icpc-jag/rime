#!/usr/bin/python

import sys
import traceback


class UiContext(object):
    """UI object of Rime."""

    def __init__(self, options, console, commands, graph):
        self.options = options
        self.console = console
        self.commands = commands
        self.graph = graph
        self.errors = ErrorRecorder(self)


class ErrorRecorder(object):
    """Accumurates errors/warnings and print summary of them."""

    def __init__(self, ui):
        self.ui = ui
        self.errors = []
        self.warnings = []

    def Error(self, source, reason, exc_info=None, quiet=False):
        """Emit an error.

        If quiet is True it is not printed immediately, but shown in summary.
        """
        msg, stacktrace = self._FormatErrorMessage(source, reason, exc_info)
        self.errors.append(msg)
        if not quiet:
            self.ui.console.PrintError(msg)
        if stacktrace:
            self.ui.console.PrintLog(stacktrace)

    def Warning(self, source, reason, exc_info=None, quiet=False):
        """Emits an warning.

        If quiet is True it is not printed immediately, but shown in summary.
        """
        msg, stacktrace = self._FormatErrorMessage(source, reason, exc_info)
        self.warnings.append(msg)
        if not quiet:
            self.ui.console.PrintWarning(msg)
        if stacktrace:
            self.ui.console.PrintLog(stacktrace)

    def Exception(self, source, exc_info=None, quiet=False):
        """Emits an exception without aborting.

        If exc_info is not given, use current context.
        If quiet is True it is not printed immediately, but shown in summary.
        """
        if exc_info is None:
            exc_info = sys.exc_info()
        self.Error(source, str(exc_info[1]), exc_info=exc_info, quiet=quiet)

    def HasError(self):
        return bool(self.errors)

    def HasWarning(self):
        return bool(self.warnings)

    def PrintSummary(self):
        for e in self.errors:
            self.ui.console.PrintError(e)
        for e in self.warnings:
            self.ui.console.PrintWarning(e)
        self.ui.console.Print(
            'Total %d errors, %d warnings' %
            (len(self.errors), len(self.warnings)))

    def _FormatErrorMessage(self, source, reason, exc_info):
        msg, stacktrace = '', None
        if source:
            msg += '%s: ' % source.fullname
        msg += '%s' % reason
        if exc_info is not None and self.ui.options.debug >= 1:
            stackframes = traceback.extract_tb(exc_info[2])
            filename, lineno, modulename, code = stackframes[-1]
            msg += ' [File "%s", line %d, in %s]' % (
                filename, lineno, modulename)
            stacktrace = ''.join(traceback.format_list(stackframes))
        return (msg, stacktrace)
