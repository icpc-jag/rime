#!/usr/bin/python

RIMEROOT_FILE = 'RIMEROOT'
PROBLEM_FILE = 'PROBLEM'
SOLUTION_FILE = 'SOLUTION'
TESTS_FILE = 'TESTS'

STAMP_FILE = '.stamp'

IN_EXT = '.in'
DIFF_EXT = '.diff'
OUT_EXT = '.out'
EXE_EXT = '.exe'
JUDGE_EXT = '.judge'
CACHE_EXT = '.cache'
LOG_EXT = '.log'
VALIDATION_EXT = '.validation'

RIME_OUT_DIR = 'rime-out'


# Limit the width of help messages to 75 characters!

GLOBAL_HELP = """\
Rime is a tool for programming contest organizers to automate usual, boring
and error-prone process of problem set preparation. It supports various
programming contest styles like ACM-ICPC, TopCoder, etc. by plugins.

To see a brief description and available options of a command, try:

rime.py help <command>
"""

BUILD_HELP = """\
If the target is a project, Rime builds all problems recursively.

If the target is a problem, Rime builds all solutions and a testset
recursively.

If the target is a solution, Rime compiles the solution program specified
in SOLUTION file.

If the target is a testset, Rime compiles all necessary programs including
input generators, input validators, output judges, and a reference solution
that is automatically selected or explicitly specified in PROBLEM file.
Then it copies static input/output files (*.in, *.diff) into rime-out
directory, runs input generators, runs input validators against all
static/generated input files, and finally runs a reference solution over
them to generate reference output files.

<target> can be omitted to imply the target in the current working
directory.

If -k (--keep_going) is set, build does not stop even if a compile error
happens.

-j (--jobs) can be used to make build faster to allow several processes to
run in parallel.
"""

TEST_HELP = """\
If the target is a project, Rime runs tests of all problems recursively.

If the target is a problem, Rime runs tests of all solutions recursively.

If the target is a solution, Rime builds it and the testset of the problem,
and then runs the solution against a series of tests.

If the target is a testset, Rime runs tests of all solutions recursively.

<target> can be omitted to imply the target in the current working
directory.

If -k (--keep_going) is set, build does not stop even if a compile error
or a test failure happens.

-j (--jobs) can be used to make build and test faster to allow several
processes to run in parallel. If a test failed by time limit exceed in
parallelized tests, the same test is re-run after all other concurrent
processes are finished to see if it really does not run in the specified
time limit. You can always force this behavior not to run tests
concurrently by -p (--precise).

If -C (--cache_tests) is set, Rime skips unchanged tests which passed
previously.
"""

CLEAN_HELP = """\
Deletes files under corresponding directory in rime-out.

<target> can be omitted to imply the target in the current working
directory.
"""
