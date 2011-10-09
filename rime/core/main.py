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

import os
import os.path
import platform
import sys
import traceback

from rime.core import commands as commands_mod
from rime.core import hooks
from rime.core import targets
from rime.core import taskgraph
from rime.core import ui as ui_mod
from rime.util import console as console_mod
from rime.util import module_loader
from rime.util import struct


def LoadRequiredModules():
  # TODO(nya): Fix this hacky implementation.
  module_loader.LoadPackage('rime.basic')
  while True:
    commands = commands_mod.GetCommands()
    default_options = struct.Struct(commands[None].GetDefaultOptionDict())
    null_console = console_mod.NullConsole()
    graph = taskgraph.SerialTaskGraph()
    fake_ui = ui_mod.UiContext(default_options, null_console, commands, graph)
    try:
      LoadProject(os.getcwd(), fake_ui)
      break
    except targets.ConfigurationError:
      # Configuration errors should be processed later.
      break
    except targets.ReloadConfiguration:
      # Processed use_plugin(). Retry.
      pass


def CheckSystem(ui):
  """Checks the sytem environment."""
  system = platform.system()
  if system in ('Windows', 'Microsoft') or system.startswith('CYGWIN'):
    ui.console.Print('Note: Running Rime under Windows will be unstable.')
  return True


def LoadProject(cwd, ui):
  """Loads configs and return Project instance.

  Location of root directory is searched upward from cwd.
  If PROJECT cannot be found, return None.
  """
  path = cwd
  while not targets.registry.Project.CanLoadFrom(path):
    (head, tail) = os.path.split(path)
    if head == path:
      return None
    path = head
  project = targets.registry.Project(None, path, None)
  try:
    project.Load(ui)
    return project
  except targets.ConfigurationError:
    ui.errors.Exception(project)
    return None


def CreateTaskGraph(options):
  """Creates the instance of TaskGraph to use for this session."""
  if options.parallelism == 0:
    graph = taskgraph.SerialTaskGraph()
  else:
    graph = taskgraph.FiberTaskGraph(
      parallelism=options.parallelism,
      debug=options.debug)
  return graph


def InternalMain(argv):
  """Main method called when invoked as stand-alone script."""
  LoadRequiredModules()

  console = console_mod.TtyConsole(sys.stdout)

  commands = commands_mod.GetCommands()

  # Parse arguments.
  try:
    cmd, args, options = commands_mod.Parse(argv, commands)
  except commands_mod.ParseError, e:
    console.PrintError(str(e))
    return 1

  graph = CreateTaskGraph(options)

  ui = ui_mod.UiContext(options, console, commands, graph)

  if options.help:
    cmd.PrintHelp(ui)
    return 0

  # Check system.
  if not CheckSystem(ui):
    return 1

  # Try to load config files.
  project = LoadProject(os.getcwd(), ui)
  if ui.errors.HasError():
    return 1
  if not project:
    console.PrintError('PROJECT not found. Make sure you are in Rime subtree.')
    return 1

  # Run the task.
  task = None
  try:
    hooks.pre_command(ui)
    task = cmd.Run(project, tuple(args), ui)
    if task:
      graph.Run(task)
    hooks.post_command(ui)
  except KeyboardInterrupt:
    if ui.options.debug >= 1:
      traceback.print_exc()
    raise

  if task:
    console.Print()
    console.Print(console.BOLD, 'Error Summary:', console.NORMAL)
    ui.errors.PrintSummary()
  return 0


def Main(args):
  try:
    # Instanciate Rime class and call Main().
    return InternalMain(args)
  except SystemExit:
    raise
  except KeyboardInterrupt:
    # Suppress stack trace when interrupted by Ctrl-C
    return 1
  except:
    # Print stack trace for debug.
    exc = sys.exc_info()
    sys.excepthook(*exc)
    return 1
