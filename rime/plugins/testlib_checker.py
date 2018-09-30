#!/usr/bin/python

# using testlib

import os.path
import subprocess

from rime.core import codes
from rime.core import taskgraph
from rime.util import files


class TestlibCode(codes.registry.CXXCode):
    PREFIX = 'testlib'
    EXTENSIONS = []

    def __init__(self, src_name, src_dir, out_dir, flags=[], testlib=None):
        super(TestlibCode, self).__init__(src_name, src_dir, out_dir, flags)
        self.testlib = testlib

    @taskgraph.task_method
    def Compile(self):
        """Compile the code and return RunResult."""
        if self.testlib is not None:
            files.CopyFile(
                os.path.join(self.src_dir, self.testlib),
                os.path.join(self.out_dir, 'testlib.h'))
        try:
            if not self.compile_args:
                result = codes.RunResult(codes.RunResult.OK, None)
            else:
                result = yield self._ExecForCompile(args=self.compile_args)
        except Exception as e:
            result = codes.RunResult('On compiling: %s' % e, None)
        yield result

    @taskgraph.task_method
    def _ExecForCompile(self, args):
        with open(os.path.join(self.out_dir, self.log_name), 'w') as outfile:
            yield (yield self._ExecInternal(
                args=args, cwd=self.out_dir,
                stdin=files.OpenNull(), stdout=outfile,
                stderr=subprocess.STDOUT))

    @taskgraph.task_method
    def Run(self, args, cwd, input, output, timeout, precise,
            redirect_error=False):
        """Run the code and return RunResult."""
        try:
            # reorder
            result = yield self._ExecForRun(
                args=tuple(list(self.run_args) + [args[1], args[5], args[3]]),
                cwd=cwd, input=input, output=output, timeout=timeout,
                precise=precise, redirect_error=redirect_error)
        except Exception as e:
            result = codes.RunResult('On execution: %s' % e, None)
        yield result


codes.registry.Add(TestlibCode)
