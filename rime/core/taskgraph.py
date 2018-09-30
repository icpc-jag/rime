#!/usr/bin/python

"""A framework for parallel processing in single-threaded environment."""


import functools
import os
import signal
import subprocess
import sys
import threading
import time

from six import reraise

# State of tasks.
NUM_STATES = 6
RUNNING, WAITING, BLOCKED, READY, FINISHED, ABORTED = range(NUM_STATES)


class TaskBranch(object):
    def __init__(self, tasks, unsafe_interrupt=False):
        self.tasks = tasks
        self.interrupt = unsafe_interrupt


class TaskReturn(object):
    def __init__(self, value):
        self.value = value


class TaskBlock(object):
    pass


class _TaskRaise(object):
    """Internal only; don't return an instance of this class from generators"""

    def __init__(self, type, value=None, traceback=None):
        self.exc_info = (type, value, traceback)


class Bailout(Exception):
    def __init__(self, value=None):
        self.value = value


class TaskInterrupted(Exception):
    pass


class Task(object):
    def __hash__(self):
        """Hash function of Task.

        Usually users should override CacheKey() only.
        """
        if self.CacheKey() is None:
            return id(self)
        return hash(self.CacheKey())

    def __eq__(self, other):
        """Equality function of Task.

        Usually users should override CacheKey() only.
        """
        if not isinstance(other, Task):
            return False
        if self.CacheKey() is None and other.CacheKey() is None:
            return id(self) == id(other)
        return self.CacheKey() == other.CacheKey()

    def IsCacheable(self):
        """Checks if this task is cachable.

        Usually users should override CacheKey() only.
        """
        return self.CacheKey() is not None

    def IsExclusive(self):
        """Checks if this task is exclusive.

        If a task is exclusive, it runs only when no other task is blocked.
        """
        return False

    def CacheKey(self):
        """Returns the cache key of this task.

        Need to be overridden in subclasses.
        If this returns None, the task value is never cached.
        """
        raise NotImplementedError()

    def Continue(self, value=None):
        """Continues the task.

        Implementations can return these type of values:
        - TaskBranch: a list of tasks to be invoked next.
        - TaskReturn: a value to be returned to the caller.
        - TaskBlock: indicates this operation will block.
        - Task: treated as TaskBranch(task).
        - any other value: treated as TaskReturn(value).
        In addition to these, it can raise an exception, including Bailout.

        First invocation of this function will be with no parameter or None.
        If it returns TaskBranch, next parameter will be a list of the results
        of the specified tasks.
        """
        raise NotImplementedError()

    def Throw(self, type, value=None, traceback=None):
        """Throws in an exception.

        After Continue() or Throw() returned TaskBranch, if some of the
        branches raised an exception, this function is called. Return
        value of this function is treated in the same way as Continue().
        """
        raise NotImplementedError()

    def Poll(self):
        """Polls the blocked task.

        If the operation is ready, return True. This function should return
        immediately, and should not raise an exception.
        """
        return True

    def Wait(self):
        """Polls the blocked task.

        This function should wait until the operation gets ready. This function
        should not raise an exception.
        """
        pass

    def Close(self):
        """Closes the task.

        This is called once after Continue() or Throw() returned TaskReturn,
        they raised an exception, or the task was interrupted.
        The task should release all resources associated with it, such as
        running generators or opened processes.
        If this function raises an exception, the value returned by Continue()
        or Throw() is discarded.
        """
        pass


class GeneratorTask(Task):
    def __init__(self, it, key):
        self.it = it
        self.key = key

    def __repr__(self):
        return repr(self.key)

    def CacheKey(self):
        return self.key

    def Continue(self, value=None):
        try:
            return self.it.send(value)
        except StopIteration:
            return TaskReturn(None)

    def Throw(self, type, value=None, traceback=None):
        try:
            return self.it.throw(type, value, traceback)
        except StopIteration:
            return TaskReturn(None)

    def Close(self):
        try:
            self.it.close()
        except RuntimeError:
            # Python2.5 raises RuntimeError when GeneratorExit is ignored.
            # This often happens when yielding a return value from inside
            # of try block, or even Ctrl+C was pressed when in try block.
            pass

    @staticmethod
    def FromFunction(func):
        @functools.wraps(func)
        def MakeTask(*args, **kwargs):
            key = GeneratorTask._MakeCacheKey(func, args, kwargs)
            try:
                hash(key)
            except TypeError:
                raise ValueError(
                    'Unhashable argument was passed to GeneratorTask function')
            it = func(*args, **kwargs)
            return GeneratorTask(it, key)
        return MakeTask

    @staticmethod
    def _MakeCacheKey(func, args, kwargs):
        return ('GeneratorTask', func, tuple(args), tuple(kwargs.items()))


# Shortcut for daily use.
task_method = GeneratorTask.FromFunction


class ExternalProcessTask(Task):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.proc = None
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        else:
            self.timeout = None
        if 'exclusive' in kwargs:
            self.exclusive = kwargs['exclusive']
            del kwargs['exclusive']
        else:
            self.exclusive = False
        self.timer = None

    def CacheKey(self):
        # Never cache.
        return None

    def IsExclusive(self):
        return self.exclusive

    def Continue(self, value=None):
        if self.exclusive:
            return self._ContinueExclusive()
        else:
            return self._ContinueNonExclusive()

    def _ContinueExclusive(self):
        assert self.proc is None
        self._StartProcess()
        self.proc.wait()
        return TaskReturn(self._EndProcess())

    def _ContinueNonExclusive(self):
        if self.proc is None:
            self._StartProcess()
            return TaskBlock()
        elif not self.Poll():
            return TaskBlock()
        else:
            return TaskReturn(self._EndProcess())

    def Poll(self):
        assert self.proc is not None
        return self.proc.poll() is not None

    def Wait(self):
        assert self.proc is not None
        self.proc.wait()

    def Close(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        if self.proc is not None:
            try:
                os.kill(self.proc.pid, signal.SIGKILL)
            except Exception:
                pass
            self.proc.wait()
            self.proc = None

    def _StartProcess(self):
        self.start_time = time.time()
        self.proc = subprocess.Popen(*self.args, **self.kwargs)
        if self.timeout is not None:
            def TimeoutKiller():
                try:
                    os.kill(self.proc.pid, signal.SIGXCPU)
                except Exception:
                    pass
            self.timer = threading.Timer(self.timeout, TimeoutKiller)
            self.timer.start()
        else:
            self.timer = None

    def _EndProcess(self):
        self.end_time = time.time()
        self.time = self.end_time - self.start_time
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        # Don't keep proc in cache.
        proc = self.proc
        self.proc = None
        return proc


class SerialTaskGraph(object):
    """TaskGraph which emulates normal serialized execution."""

    def __init__(self):
        self.cache = dict()
        self.blocked_task = None
        self.running = False

    def IsRunning(self):
        return self.running

    def Run(self, task):
        assert not self.running
        self.running = True
        try:
            return self._Run(task)
        finally:
            self.running = False

    def _Run(self, task):
        if task not in self.cache:
            self.cache[task] = None
            value = (True, None)
            while True:
                try:
                    if value[0]:
                        result = task.Continue(value[1])
                    elif isinstance(value[1][1], Bailout):
                        result = task.Continue(value[1][1].value)
                    else:
                        result = task.Throw(*value[1])
                except StopIteration:
                    result = TaskReturn(None)
                except Exception:
                    result = _TaskRaise(*sys.exc_info())
                if isinstance(result, TaskBranch):
                    try:
                        value = (True, [self._Run(subtask)
                                        for subtask in result.tasks])
                    except Exception:
                        value = (False, sys.exc_info())
                elif isinstance(result, Task):
                    try:
                        value = (True, self._Run(result))
                    except Exception:
                        value = (False, sys.exc_info())
                elif isinstance(result, TaskBlock):
                    value = (True, None)
                    try:
                        self.blocked_task = task
                        task.Wait()
                    finally:
                        self.blocked_task = None
                elif isinstance(result, _TaskRaise):
                    self.cache[task] = (False, result.exc_info)
                    break
                elif isinstance(result, TaskReturn):
                    self.cache[task] = (True, result.value)
                    break
                else:
                    self.cache[task] = (True, result)
                    break
            try:
                task.Close()
            except Exception:
                self.cache[task] = (False, sys.exc_info())
        if self.cache[task] is None:
            raise RuntimeError('Cyclic task dependency found')
        success, value = self.cache[task]
        if success:
            return value
        else:
            reraise(value[0], value[1], value[2])

    def GetBlockedTasks(self):
        if self.blocked_task is not None:
            return [self.blocked_task]
        return []


class FiberTaskGraph(object):
    """TaskGraph which executes tasks with fibers (microthreads).

    FiberTaskGraph allows some tasks to be in blocked state in the same time.
    Branched tasks are executed in arbitrary order.
    """

    def __init__(self, parallelism, debug=0):
        self.parallelism = parallelism
        self.debug = debug
        self.cache = dict()
        self.task_graph = dict()
        self.task_interrupt = dict()
        self.task_counters = dict()
        self.task_waits = dict()
        self.task_state = dict()
        self.state_stats = [0] * NUM_STATES
        self.ready_tasks = []
        self.blocked_tasks = []
        self.pending_stack = []
        self.running = False

    def IsRunning(self):
        return self.running

    def Run(self, init_task):
        assert not self.running
        self.running = True
        self.first_tick = time.clock()
        self.last_tick = self.first_tick
        self.cumulative_parallelism = 0.0
        self._BranchTask(None, [init_task])
        while self._RunNextTask():
            pass
        for task in self.task_state:
            if self.task_state[task] not in (FINISHED, ABORTED):
                self._InterruptTask(task)
        self._UpdateCumulativeParallelism()
        if self.last_tick > self.first_tick:
            parallelism_efficiency = (
                self.cumulative_parallelism /
                (self.parallelism * (self.last_tick - self.first_tick)))
        else:
            parallelism_efficiency = 1.0
        self._Log('Parallelism efficiency: %.2f%%' %
                  (100.0 * parallelism_efficiency),
                  level=1)
        assert self.task_state[None] == READY
        del self.task_state[None]
        del self.task_graph[None]
        self.running = False
        success, value = self.cache[init_task]
        if success:
            return value
        elif isinstance(value, Bailout):
            return value.value
        else:
            reraise(value[0], value[1], value[2])

    def _RunNextTask(self):
        while len(self.ready_tasks) == 0:
            if not self._VisitBranch():
                self._WaitBlockedTasks()
        next_task = self.ready_tasks.pop(0)
        self._LogTaskStats()
        if next_task is None:
            return False
        if self.task_state[next_task] != READY:
            # Interrupted.
            return True
        exc_info = None
        if next_task in self.task_graph:
            if isinstance(self.task_graph[next_task], list):
                value = []
                for task in self.task_graph[next_task]:
                    if task in self.cache:
                        success, cached = self.cache[task]
                        if success:
                            value.append(cached)
                        elif exc_info is None or isinstance(
                                exc_info[1], TaskInterrupted):
                            exc_info = cached
            else:
                success, cached = self.cache[self.task_graph[next_task]]
                if success:
                    value = cached
                else:
                    exc_info = cached
            del self.task_graph[next_task]
        else:
            value = None
        self._SetTaskState(next_task, RUNNING)
        if exc_info is not None:
            if isinstance(exc_info[1], Bailout):
                self._ContinueTask(next_task, exc_info[1].value)
            else:
                self._ThrowTask(next_task, exc_info)
        else:
            self._ContinueTask(next_task, value)
        return True

    def _VisitBranch(self):
        if not self.pending_stack:
            return False
        # Visit branches by depth first.
        task, subtask = self.pending_stack.pop()
        self._BeginTask(subtask, task)
        return True

    def _ContinueTask(self, task, value):
        assert self.task_state[task] == RUNNING
        assert not task.IsExclusive() or len(self.blocked_tasks) == 0
        self._LogDebug('_ContinueTask: %s: entering' % task)
        try:
            result = task.Continue(value)
        except Exception:
            self._LogDebug('_ContinueTask: %s: exception raised' % task)
            self._ProcessTaskException(task, sys.exc_info())
        else:
            self._LogDebug('_ContinueTask: %s: exited' % task)
            self._ProcessTaskResult(task, result)

    def _ThrowTask(self, task, exc_info):
        assert self.task_state[task] == RUNNING
        assert not task.IsExclusive() or len(self.blocked_tasks) == 0
        self._LogDebug('_ThrowTask: %s: entering' % task)
        try:
            result = task.Throw(*exc_info)
        except Exception:
            self._LogDebug('_ThrowTask: %s: exception raised' % task)
            self._ProcessTaskException(task, sys.exc_info())
        else:
            self._LogDebug('_ThrowTask: %s: exited' % task)
            self._ProcessTaskResult(task, result)

    def _ProcessTaskResult(self, task, result):
        assert self.task_state[task] == RUNNING
        if isinstance(result, Task):
            self._LogDebug('_ProcessTaskResult: %s: received Task' % task)
            self._BranchTask(task, result)
        elif isinstance(result, TaskBranch):
            self._LogDebug('_ProcessTaskResult: %s: received TaskBranch '
                           'with %d tasks' % (task, len(result.tasks)))
            self._BranchTask(task, list(result.tasks), result.interrupt)
        elif isinstance(result, TaskReturn):
            self._LogDebug(
                '_ProcessTaskResult: %s: received TaskReturn' % task)
            self._FinishTask(task, result.value)
        elif isinstance(result, TaskBlock):
            self._LogDebug('_ProcessTaskResult: %s: received TaskBlock' % task)
            self._BlockTask(task)
        else:
            self._LogDebug('_ProcessTaskResult: %s: received unknown type,'
                           'implying TaskReturn' % task)
            self._FinishTask(task, result)

    def _ProcessTaskException(self, task, exc_info):
        assert self.task_state[task] == RUNNING
        try:
            task.Close()
        except Exception:
            # Ignore the exception.
            pass
        self._ExceptTask(task, exc_info)

    def _BranchTask(self, task, subtasks, interrupt=False):
        assert task is None or self.task_state[task] == RUNNING
        self.task_graph[task] = subtasks
        if not isinstance(subtasks, list):
            assert isinstance(subtasks, Task)
            subtasks = [subtasks]
        if len(subtasks) == 0:
            self._LogDebug('_BranchTask: %s: zero branch, fast return' % task)
            self.ready_tasks.insert(0, task)
            self._SetTaskState(task, READY)
            self._LogTaskStats()
            return
        self.task_interrupt[task] = interrupt
        self.task_counters[task] = len(subtasks)
        # The branches are half-expanded, but don't complete the operation here
        # so that too many branches are opened.
        for subtask in reversed(subtasks):
            self.pending_stack.append((task, subtask))
        self._SetTaskState(task, WAITING)

    def _BeginTask(self, task, parent_task):
        if task in self.cache:
            assert self.task_state[task] in (FINISHED, ABORTED)
            self._LogDebug('_BeginTask: %s: cache hit' % task)
            success = self.cache[task][0]
            if success:
                self._ResolveTask(parent_task)
            else:
                self._BailoutTask(parent_task)
        elif parent_task not in self.task_counters:
            # Some sibling task already bailed out. Skip this task.
            self._LogDebug('_BeginTask: %s: sibling task bailed out' % task)
            return
        else:
            if task in self.task_waits:
                assert self.task_state[task] in (WAITING, BLOCKED)
                self._LogDebug('_BeginTask: %s: running' % task)
                self.task_waits[task].append(parent_task)
            else:
                assert task not in self.task_state
                self._LogDebug('_BeginTask: %s: starting' % task)
                self.task_waits[task] = [parent_task]
                self._SetTaskState(task, RUNNING)
                if task.IsExclusive():
                    self._WaitBlockedTasksUntilEmpty()
                self._ContinueTask(task, None)

    def _FinishTask(self, task, value):
        assert self.task_state[task] == RUNNING
        try:
            task.Close()
        except Exception:
            self._ExceptTask(task, sys.exc_info())
            return
        self.cache[task] = (True, value)
        self._LogDebug('_FinishTask: %s: finished, returned: %s' %
                       (task, value))
        for wait_task in self.task_waits[task]:
            self._ResolveTask(wait_task)
        del self.task_waits[task]
        self._SetTaskState(task, FINISHED)

    def _ExceptTask(self, task, exc_info):
        assert self.task_state[task] in (RUNNING, BLOCKED)
        assert task not in self.cache
        self.cache[task] = (False, exc_info)
        self._LogDebug('_ExceptTask: %s: exception raised: %s' %
                       (task, exc_info[0].__name__))
        bailouts = self.task_waits[task]
        del self.task_waits[task]
        if self.task_state[task] == BLOCKED:
            del self.task_counters[task]
        self._SetTaskState(task, ABORTED)
        for bailout in bailouts:
            self._BailoutTask(bailout)

    def _BlockTask(self, task):
        assert self.task_state[task] == RUNNING
        assert len(self.blocked_tasks) < self.parallelism
        self.task_counters[task] = 1
        self._UpdateCumulativeParallelism()
        self.blocked_tasks.insert(0, task)
        self._SetTaskState(task, BLOCKED)
        self._LogTaskStats()
        self._LogDebug('_BlockTask: %s: pushed to blocked_tasks' % task)
        self._WaitBlockedTasksUntilNotFull()
        assert len(self.blocked_tasks) < self.parallelism

    def _WaitBlockedTasksUntilEmpty(self):
        self._LogDebug('_WaitBlockedTasksUntilEmpty: %d blocked tasks' %
                       len(self.blocked_tasks))
        while len(self.blocked_tasks) > 0:
            self._WaitBlockedTasks()

    def _WaitBlockedTasksUntilNotFull(self):
        self._LogDebug('_WaitBlockedTasksUntilNotFull: %d blocked tasks' %
                       len(self.blocked_tasks))
        if len(self.blocked_tasks) == self.parallelism:
            self._Log('Maximum parallelism reached, waiting for blocked tasks',
                      level=2)
            self._WaitBlockedTasks()
            self._Log('Blocked task ready (%d -> %d)' %
                      (self.parallelism, len(self.blocked_tasks)),
                      level=2)

    def _WaitBlockedTasks(self):
        assert len(self.blocked_tasks) > 0
        self._LogTaskStats()
        self._LogDebug('_WaitBlockedTasks: waiting')
        while True:
            resolved = self._PollBlockedTasks()
            if resolved > 0:
                break
            self._Sleep()
        self._LogDebug(
            '_WaitBlockedTasks: resolved %d blocked tasks' % resolved)

    def _PollBlockedTasks(self):
        i = 0
        resolved = 0
        while i < len(self.blocked_tasks):
            task = self.blocked_tasks[i]
            assert self.task_state[task] == BLOCKED
            success = task.Poll()
            if success:
                self._ResolveTask(task)
                resolved += 1
                self._UpdateCumulativeParallelism()
                self.blocked_tasks.pop(i)
                self._LogTaskStats()
            else:
                i += 1
        return resolved

    def _ResolveTask(self, task):
        if task not in self.task_counters:
            self._LogDebug(
                '_ResolveTask: %s: resolved, but already bailed out' % task)
            return
        assert self.task_state[task] in (WAITING, BLOCKED)
        self._LogDebug(
            '_ResolveTask: %s: resolved, counter: %d -> %d' %
            (task, self.task_counters[task], self.task_counters[task] - 1))
        self.task_counters[task] -= 1
        if self.task_counters[task] == 0:
            if task in self.task_graph and isinstance(
                    self.task_graph[task], list):
                # Multiple branches.
                self.ready_tasks.append(task)
            else:
                # Serial execution or blocked task.
                self.ready_tasks.insert(0, task)
            if task in self.task_interrupt:
                del self.task_interrupt[task]
            del self.task_counters[task]
            self._SetTaskState(task, READY)
            self._LogDebug('_ResolveTask: %s: pushed to ready_task' % task)
            self._LogTaskStats()

    def _BailoutTask(self, task):
        if task not in self.task_counters:
            self._LogDebug('_BailoutTask: %s: multiple bail out' % task)
            return
        assert self.task_state[task] in (WAITING, BLOCKED)
        self._LogDebug('_BailoutTask: %s: bailing out' % task)
        if task in self.task_graph and isinstance(self.task_graph[task], list):
            # Multiple branches.
            self.ready_tasks.append(task)
        else:
            # Serial execution or blocked task.
            self.ready_tasks.insert(0, task)
        interrupt = False
        if task in self.task_interrupt:
            interrupt = self.task_interrupt[task]
            del self.task_interrupt[task]
        del self.task_counters[task]
        self._SetTaskState(task, READY)
        self._LogDebug('_BailoutTask: %s: pushed to ready_task' % task)
        if interrupt and task in self.task_graph:
            for subtask in self.task_graph[task]:
                self._InterruptTask(subtask)

    def _InterruptTask(self, task):
        if (task is None or task not in self.task_state or
                self.task_state[task] not in (WAITING, BLOCKED, READY)):
            return
        self._LogDebug('_InterruptTask: %s: interrupted' % task)
        try:
            task.Close()
        except Exception:
            pass
        # Simulate as if the task raised an exception.
        subtasks = []
        if task in self.task_graph:
            subtasks = self.task_graph[task]
            del self.task_graph[task]
            if not isinstance(subtasks, list):
                subtasks = [subtasks]
        if task in self.task_interrupt:
            del self.task_interrupt[task]
        if task in self.task_counters:
            del self.task_counters[task]
        if self.task_state[task] == BLOCKED:
            self._UpdateCumulativeParallelism()
            self.blocked_tasks.remove(task)
        self._SetTaskState(task, RUNNING)
        self._ExceptTask(task, (TaskInterrupted, TaskInterrupted(), None))
        for subtask in subtasks:
            self._InterruptTask(subtask)

    def _UpdateCumulativeParallelism(self):
        cur_tick = time.clock()
        self.cumulative_parallelism += (
            (cur_tick - self.last_tick) * len(self.blocked_tasks))
        self.last_tick = cur_tick

    def _Sleep(self):
        time.sleep(0.01)

    def _SetTaskState(self, task, state):
        if self.debug >= 1:
            if state == RUNNING:
                assert task not in self.cache
                assert task not in self.task_graph
                assert task not in self.task_interrupt
                assert task not in self.task_counters
                assert task is None or task in self.task_waits
            elif state == WAITING:
                assert task not in self.cache
                assert task in self.task_graph
                assert task in self.task_interrupt
                assert task in self.task_counters
                assert task is None or task in self.task_waits
            elif state == BLOCKED:
                assert task not in self.cache
                assert task not in self.task_graph
                assert task not in self.task_interrupt
                assert self.task_counters.get(task) == 1
                assert task in self.task_waits
            elif state == READY:
                assert task not in self.cache
                assert task not in self.task_interrupt
                assert task not in self.task_counters
                assert task is None or task in self.task_waits
            elif state == FINISHED:
                assert task in self.cache and self.cache[task][0]
                assert task not in self.task_graph
                assert task not in self.task_interrupt
                assert task not in self.task_counters
                assert task not in self.task_waits
            elif state == ABORTED:
                assert task in self.cache and not self.cache[task][0]
                assert task not in self.task_graph
                assert task not in self.task_interrupt
                assert task not in self.task_counters
                assert task not in self.task_waits
            else:
                raise AssertionError('Unknown state: ' + str(state))
        if task in self.task_state:
            self.state_stats[self.task_state[task]] -= 1
        self.state_stats[state] += 1
        self.task_state[task] = state

    def _LogTaskStats(self):
        if self.debug == 0:
            return
        self._LogDebug(('RUNNING %d, WAITING %d, BLOCKED %d, '
                        'READY %d, FINISHED %d, ABORTED %d') %
                       tuple(self.state_stats))

    def _Log(self, msg, level):
        if self.debug >= level:
            # TODO(nya): Do real logging.
            pass

    def _LogDebug(self, msg):
        self._Log(msg, level=3)

    def GetBlockedTasks(self):
        return self.blocked_tasks[:]
