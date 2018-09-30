#!/usr/bin/python

from rime.core import commands


class Example(commands.CommandBase):
    def __init__(self, parent):
        super(Example, self).__init__(
            'example',
            '',
            'Example command.',
            'Example help.',
            parent)

    def Run(self, project, args, ui):
        ui.console.Print('Hello, world!')
        ui.console.Print()
        ui.console.Print('Project:')
        ui.console.Print('  %s' % repr(project))
        ui.console.Print()
        ui.console.Print('Parameters:')
        for i, arg in enumerate(args):
            ui.console.Print('  args[%s] = "%s"' % (i, arg))
        ui.console.Print()
        ui.console.Print('Options:')
        for key, value in ui.options.items():
            ui.console.Print('  options.%s = %s' % (key, value))


commands.registry.Add(Example)
