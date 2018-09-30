#!/usr/bin/python

from rime.util import class_registry
from rime.util import struct


class ParseError(Exception):
    pass


class OptionEntry(object):
    def __init__(self, shortname, longname, varname, argtype, argdef, argname,
                 description):
        assert argtype in (bool, int, str)
        assert isinstance(argdef, argtype)
        self.shortname = shortname
        self.longname = longname
        self.varname = varname
        self.argtype = argtype
        self.argdef = argdef
        self.argname = argname
        self.description = description

    def Match(self, name):
        return (name in (self.shortname, self.longname))


class Command(object):
    name = None
    description = None

    def __init__(self, parent):
        self.parent = parent

    def FindOptionEntry(self, name):
        raise NotImplementedError()

    def GetDefaultOptionDict(self):
        raise NotImplementedError()

    def PrintHelp(self, ui):
        raise NotImplementedError()

    def Run(self, project, args, ui):
        raise NotImplementedError()


class CommandBase(Command):
    def __init__(self, name, args, oneline_summary, description, parent):
        super(CommandBase, self).__init__(parent)
        self.name = name
        self.args = args
        self.oneline_summary = oneline_summary
        self.description = description
        self.options = []

    def AddOptionEntry(self, option):
        self.options.append(option)

    def FindOptionEntry(self, name):
        for option in self.options:
            if option.Match(name):
                return option
        if self.parent:
            return self.parent.FindOptionEntry(name)
        return None

    def GetDefaultOptionDict(self):
        if self.parent:
            options = self.parent.GetDefaultOptionDict()
        else:
            options = {}
        for option in self.options:
            assert option.varname not in options
            options[option.varname] = option.argdef
        return options

    def PrintHelp(self, ui):
        ui.console.Print('rime.py %s [<options>...] %s' %
                         (self.name or '<command>', self.args or
                          '[<args>...]'))
        ui.console.Print()
        self._PrintCommandDescription(ui)
        if self.name:
            ui.console.Print('Options for "%s":' % self.name)
            ui.console.Print()
            self._PrintOptionDescription(ui)
        ui.console.Print('Global options:')
        ui.console.Print()
        ui.commands[None]._PrintOptionDescription(ui)

    def _PrintCommandDescription(self, ui):
        if self.oneline_summary:
            ui.console.Print(self.oneline_summary)
            ui.console.Print()
        if self.description:
            for line in self.description.splitlines():
                ui.console.Print('    ' + line)
            ui.console.Print()

        if not self.name:
            rows = []
            values = filter(lambda a: a.name, ui.commands.values())
            for cmd in sorted(values, key=lambda a: a.name):
                rows.append((' %s    ' % cmd.name, cmd.oneline_summary))

            offset = max([len(left_col) for left_col, _ in rows])

            ui.console.Print('Commands:')
            ui.console.Print()
            for left_col, right_col in rows:
                ui.console.Print(left_col.ljust(offset) + right_col)
            ui.console.Print()

    def _PrintOptionDescription(self, ui):
        rows = []
        for option in sorted(self.options, key=lambda a: a.longname):
            longopt = '--%s' % option.longname
            if option.argname:
                longopt += ' <%s>' % option.argname
            if option.shortname:
                left_col_head = ' -%s, %s  ' % (option.shortname, longopt)
            else:
                left_col_head = '     %s  ' % longopt
            rows.append((left_col_head, option.description.splitlines()))
        if not rows:
            ui.console.Print(' No options.')
        else:
            offset = max([len(left_col) for left_col, _ in rows])
            for left_col_head, right_col_lines in rows:
                for i, right_col_line in enumerate(right_col_lines):
                    left_col_line = (i == 0 and left_col_head or '').ljust(
                        offset)
                    ui.console.Print(left_col_line + right_col_line)
        ui.console.Print()


registry = class_registry.ClassRegistry(Command)


def GetCommands():
    commands = {}
    default = registry.Default(None)
    commands[None] = default
    for name, clazz in registry.classes.items():
        if name == 'Default':
            continue
        cmd = clazz(default)
        commands[cmd.name] = cmd
    return commands


def GetCommand(cmdname):
    return GetCommands()[cmdname]


def Parse(argv, commands):
    """Parses the command line arguments.

    Arguments:
      argv: A list of string passed to the command.
          Note that this should include sys.argv[0] as well.

    Returns:
      A tuple of (cmd_name, extra_args, options) where:
        cmd: Command object of the main command specified by the command line.
        extra_args: A list of extra arguments given to the command.
        options: Struct containing option arguments.

    Raises:
      ParseError: When failed to parse arguments.
    """
    default = commands[None]
    cmd = None
    extra_args = []
    options = default.GetDefaultOptionDict()

    assert len(argv) >= 1
    i = 1
    option_finished = False

    while i < len(argv):
        arg = argv[i]
        i += 1

        if option_finished or not arg.startswith('-'):
            if cmd is None:
                arg = arg.lower()

                if arg not in commands:
                    raise ParseError('Unknown command: %s' % arg)
                cmd = commands[arg]
                options.update(cmd.GetDefaultOptionDict())

            else:
                extra_args.append(arg)

        else:
            longopt = arg.startswith('--')
            optvalue = None

            if longopt:
                optname = arg[2:]
                if optname == '':
                    option_finished = True
                    continue
                if '=' in optname:
                    sep = optname.find('=')
                    optvalue = optname[sep + 1:]
                    optname = optname[:sep]
                optnames = [optname]

            else:
                optnames = arg[1:]

            for optname in optnames:
                optfull = '%s%s' % (longopt and '--' or '-', optname)

                option = (cmd and cmd.FindOptionEntry(optname) or
                          default.FindOptionEntry(optname))
                if option is None:
                    raise ParseError('Unknown option: %s' % optfull)

                if option.argtype is bool:
                    optvalue = True
                elif optvalue is None:
                    if i == len(argv):
                        raise ParseError(
                            'Option parameter was missing for %s' % optfull)
                    optvalue = argv[i]
                    i += 1

                try:
                    optvalue = option.argtype(optvalue)
                except Exception:
                    raise ParseError(
                        'Invalid option parameter for %s' % optfull)

                options[option.varname] = optvalue

    if cmd is None:
        cmd = commands[None]
        options['help'] = True

    return (cmd, extra_args, struct.Struct(options))


class Help(CommandBase):
    def __init__(self, parent):
        super(Help, self).__init__(
            'help',
            '<command>',
            'Show help.',
            'To see a brief description and available options of a command,'
            'try:\n'
            '\n'
            'rime.py help <command>',
            parent)

    def Run(self, project, args, ui):
        commands = GetCommands()
        cmd = None
        if len(args) > 0:
            cmd = commands.get(args[0])
        if not cmd:
            cmd = self
        cmd.PrintHelp(ui)
        return None


registry.Add(Help)
