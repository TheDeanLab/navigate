# Multiprocessing to spread CPU load, threading for concurrency:
import multiprocessing as mp
import threading

# Printing from a child process is tricky:
import io
from contextlib import redirect_stdout

# Handling exceptions from a child process/thread is tricky:
import sys
import traceback
import inspect

# Making sure objects are cleaned up nicely is tricky:
import weakref

# Making sure a child process closes when the parent exits is tricky:
import atexit
import signal

import logging
import numpy as np

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

# Sharing memory between child processes is tricky:
try:
    from multiprocessing import shared_memory
except ImportError:
    print("Warning - multiprocessing.shared_memory module could not be imported.")
    print("Shared memory arrays not implemented.")
    shared_memory = np.ndarray([0])
    # np = None

""" Created by Nathaniel H. Thayer and Andrew G. York

Full docstring at https://github.com/AndrewGYork/tools/blob/master/concurrency_tools.py.
"""


class SharedNDArray(np.ndarray):
    """A numpy array that lives in shared memory

    Inputs and outputs to/from ObjectInSubprocess are 'serialized', which
    is pretty fast - except for large in-memory objects. The only large
    in-memory objects we regularly deal with are numpy arrays, so it
    makes sense to provide a way to pass large numpy arrays via shared memory
    (which avoids slow serialization).

    Maybe you wanted to write code that looks like this:

        data_buf = np.zeros((400, 2000, 2000), dtype='uint16')
        display_buf = np.zeros((2000, 2000), dtype='uint8')

        camera = Camera()
        preprocessor = Preprocessor()
        display = Display()

        camera.record(num_images=400, out=data_buf)
        preprocessor.process(in=data_buf, out=display_buf)
        display.show(display_buf)

    ...but instead you write code that looks like this:

        data_buf = SharedNDArray(shape=(400, 2000, 2000), dtype='uint16')
        display_buf = SharedNDArray(shape=(2000, 2000), dtype='uint8')

        camera = ObjectInSubprocess(Camera)
        preprocessor = ObjectInSubprocess(Preprocessor)
        display = ObjectInSubprocess(Display)

        camera.record(num_images=400, out=data_buf)
        preprocessor.process(in=data_buf, out=display_buf)
        display.show(display_buf)

    ...and your payoff is, each object gets its own CPU core, AND passing
    large numpy arrays between the processes is still really fast!

    To implement this we used memmap from numpy.core as a template.
    """

    def __new__(
        cls,
        shape=None,
        dtype=float,
        shared_memory_name=None,
        offset=0,
        strides=None,
        order=None,
    ):
        if shared_memory_name is None:
            dtype = np.dtype(dtype)
            requested_bytes = np.prod(shape, dtype="uint64") * dtype.itemsize
            requested_bytes = int(requested_bytes)
            try:
                shm = shared_memory.SharedMemory(create=True, size=requested_bytes)
            except OSError as e:
                if e.args == (24, "Too many open files"):
                    raise OSError(
                        "You tried to simultaneously open more "
                        "SharedNDArrays than are allowed by your system!"
                    ) from e
                else:
                    raise e
            must_unlink = True  # This process is responsible for unlinking
        else:
            shm = shared_memory.SharedMemory(name=shared_memory_name, create=False)
            must_unlink = False
        obj = super(SharedNDArray, cls).__new__(
            cls, shape, dtype, shm.buf, offset, strides, order
        )
        obj.shared_memory = shm
        obj.offset = offset
        if must_unlink:
            weakref.finalize(obj, shm.unlink)
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        if not isinstance(obj, SharedNDArray):
            raise ValueError("You can't view non-shared memory as shared memory.")
        if hasattr(obj, "shared_memory") and np.may_share_memory(self, obj):
            self.shared_memory = obj.shared_memory
            self.offset = obj.offset
            self.offset += (
                self.__array_interface__["data"][0] - obj.__array_interface__["data"][0]
            )

    def __array_wrap__(self, arr, context=None):
        arr = super().__array_wrap__(arr, context)

        # Return a SharedNDArray if a SharedNDArray was given as the
        # output of the ufunc. Leave the arr class unchanged if self is not
        # a SharedNDArray to keep original SharedNDArray subclasses
        # behavior.

        if self is arr or type(self) is not SharedNDArray:
            return arr
        # Return scalar instead of 0d SharedMemory, e.g. for np.sum with
        # axis=None
        if arr.shape == ():
            return arr[()]
        # Return ndarray otherwise
        return arr.view(np.ndarray)

    def __getitem__(self, index):
        res = super().__getitem__(index)
        if type(res) is SharedNDArray and not hasattr(res, "shared_memory"):
            return res.view(type=np.ndarray)
        return res

    def __reduce__(self):
        args = (
            self.shape,
            self.dtype,
            self.shared_memory.name,
            self.offset,
            self.strides,
            None,
        )
        return SharedNDArray, args


class ResultThread(threading.Thread):
    """threading.Thread with all the simple features we wish it had.

    We added a 'get_result' method that returns values/raises exceptions.

    We changed the return value of 'start' from 'None' to 'self' -- just to
    trivially save us a line of code when launching threads.

    Example:
    ```
        def f(a):
            ''' A function that does something... '''
            return a.sum()

        ##
        ## Getting Results:
        ##
        a = np.ones((2,), dtype='uint8')

        # Our problem:
        th = threading.Thread(target=f, args=(a,))
        th.start()
        th.join() # We can't access the result of f(a) without redefining f!

        # Our solution:
        res_th = ResultThread(target=f, args=(a,)).start()
        res = res_th.get_result() # returns f(a)
        assert res == 2

        ##
        ## Error handling
        ##
        a = 1

        # Our problem:
        th = threading.Thread(target=f, args=(a,))
        th.start()
        th.join()
        # f(a) raised an unhandled exception. Our parent thread has no idea!

        # Our solution:
        res_th = ResultThread(target=f, args=(a,)).start()
        try:
            res = res_th.get_result()
        except AttributeError:
            print("AttributeError was raised in thread!")
        else:
            raise AssertionError(
                'We expected an AttributeError to be raised on join!')

        # Unhandled exceptions raised during evaluation of 'f' are reraised in
        # the parent thread when you call 'get_result'.
        # Tracebacks may print to STDERR when the exception occurs in
        # the child thread, but don't affect the parent thread (yet).
    ```
    NOTE: This module modifies threading.excepthook. You can't just copy/paste
    this class definition and expect it to work.
    """

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        super().__init__(group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def start(self):
        try:
            super().start()
        except RuntimeError as e:
            if e.args == ("can't start new thread",):
                print("*" * 80)
                print("Failed to launch a thread.")
                print(threading.active_count(), "threads are currently active.")
                print("You might have reached a limit of your system;")
                print("let some of your threads finish before launching more.")
                print("*" * 80)
            raise
        return self

    def get_result(self, timeout=None):
        """Either returns a value or raises an exception.

        Optionally accepts a timeout in seconds. If thread has not returned
        after timeout seconds, raises a TimeoutError.
        """
        super().join(timeout=timeout)
        if self.is_alive():  # Thread could potentially not be done yet!
            return TimeoutError("Thread did not return!")
        if hasattr(self, "exc_value"):
            raise self.exc_value
        return self._return


class CustodyThread(ResultThread):
    """Threads that can access shared resources in the order they were launched.

    See the docstring at the top of this module for examples.
    """

    def __init__(
        self,
        first_resource=None,
        group=None,
        target=None,
        name=None,
        args=(),
        kwargs=None,
    ):
        if "custody" not in inspect.signature(target).parameters:
            raise ValueError(
                "The function 'target' passed to a CustodyThread"
                " must accept an argument named 'custody'"
            )
        custody = _Custody()  # Useful for synchronization in the launched thread
        if first_resource is not None:
            # Get in line for custody of the first resource the launched
            # thread will use, but don't *wait* in that line; the launched
            # thread should do the waiting, not the main thread:
            custody.switch_from(None, first_resource, wait=False)
        if kwargs is None:
            kwargs = {}
        if "custody" in kwargs:
            raise ValueError(
                "CustodyThread will create and pass a keyword argument to"
                " 'target' named 'custody', so keyword arguments to a"
                " CustodyThread can't be named 'custody'"
            )
        kwargs["custody"] = custody
        super().__init__(group, target, name, args, kwargs)
        self.custody = custody


_original_threading_excepthook = threading.excepthook


def _my_threading_excepthook(args):
    """Show a traceback when a child exception isn't handled by the parent."""
    if isinstance(args.thread, ResultThread):
        args.thread.exc_value = args.exc_value
        args.thread.exc_traceback = args.exc_traceback
        args.thread.exc_type = args.exc_type
    else:
        _try_to_print_child_traceback(args.exc_value)
    return _original_threading_excepthook(args)


threading.excepthook = _my_threading_excepthook

FancyThread = ResultThread  # So Andy can refer to it like this.
PoliteThread = CustodyThread


class ObjectInSubprocess:
    def __init__(
        self,
        initializer,
        *initargs,
        custom_loop=None,
        close_method_name=None,
        closeargs=None,
        closekwargs=None,
        with_lock=False,
        **initkwargs,
    ):
        """
        Make an object in a child process, that acts like it isn't.

        As much as possible, we try to make instances of ObjectInSubprocess
        behave as if they're an instance of the object living in the parent
        process. They're not, of course: they live in a child process. If you
        have spare cores on your machine, this turns CPU-bound operations
        (which  threading can't parallelize) into IO-bound operations (which
        threading CAN parallelize),  without too much mental overhead for the
        coder.

        initializer -- callable that returns an instance of a Python object
        initargs, initkwargs --  arguments to 'initializer'
        close_method_name -- string, optional, name of our object's method to
            be called automatically when the child process exits
        closeargs, closekwargs -- arguments to 'close_method'
        """
        # Put an instance of the Python object returned by 'initializer'
        # in a child process:
        parent_pipe, child_pipe = mp.Pipe()
        child_loop = _child_loop if custom_loop is None else custom_loop
        child_process = mp.Process(
            target=child_loop,
            name=initializer.__name__,
            args=(
                child_pipe,
                initializer,
                initargs,
                initkwargs,
                close_method_name,
                closeargs,
                closekwargs,
            ),
        )
        # Attribute-setting looks weird here because we override __setattr__,
        # and because we use a dummy object's namespace to hold our attributes
        # so we shadow as little of the object's namespace as possible:
        super().__setattr__("_", _DummyClass())  # Weird, but for a reason.
        self._.parent_pipe = parent_pipe
        self._.parent_pipe_lock = _ObjectInSubprocessPipeLock()
        self._.child_pipe = child_pipe
        self._.child_process = child_process
        self._.waiting_list = _WaitingList()
        if with_lock:
            self._.resource_lock = threading.Lock()
        else:
            self._.resource_lock = None
        # Make sure the child process initialized successfully:
        with self._.parent_pipe_lock:
            self._.child_process.start()
            assert _get_response(self) == "Successfully initialized"
        # Try to ensure the child process closes when we exit:
        dummy_namespace = getattr(self, "_")
        weakref.finalize(self, _close, dummy_namespace)
        try:
            signal.signal(signal.SIGTERM, lambda s, f: _close(dummy_namespace))
        except ValueError:  # We are probably starting from a thread.
            pass  # Signal handling can only happen from main thread

    def __getattr__(self, name):
        """Access attributes of the child-process object in the parent process.

        As much as possible, we want attribute access and method calls
        to *seem* like they're happening in the parent process, if
        possible, even though they actually involve asking the child
        process over a pipe.
        """
        if self._.resource_lock:
            self._.resource_lock.acquire()
        if name == "terminate":
            with self._.parent_pipe_lock:
                self._.parent_pipe.send(None)
                self._.child_process.terminate()
            if self._.resource_lock:
                self._.resource_lock.release()
            return _dummy_function
        with self._.parent_pipe_lock:
            self._.parent_pipe.send(("__getattribute__", (name,), {}))
            attr = _get_response(self)
        if callable(attr):

            def attr(*args, **kwargs):
                with self._.parent_pipe_lock:
                    self._.parent_pipe.send((name, args, kwargs))
                    return _get_response(self, True)

        elif self._.resource_lock:
            self._.resource_lock.release()
        return attr

    def __setattr__(self, name, value):
        with self._.parent_pipe_lock:
            self._.parent_pipe.send(("__setattr__", (name, value), {}))
            return _get_response(self)


def _get_response(object_in_subprocess, release=False):
    """
    Effectively a method of ObjectInSubprocess, but defined externally to
    minimize shadowing of the object's namespace
    """
    resp, printed_output = object_in_subprocess._.parent_pipe.recv()
    if len(printed_output) > 0:
        print(printed_output, end="")
    if isinstance(resp, Exception):
        raise resp
    if (
        release
        and object_in_subprocess._.resource_lock
        and object_in_subprocess._.resource_lock.locked()
    ):
        object_in_subprocess._.resource_lock.release()
    return resp


def _close(dummy_namespace):
    """Externally defined close function.

    Effectively a method of ObjectInSubprocess, but defined externally to
    minimize shadowing of the object's namespace
    """
    if not dummy_namespace.child_process.is_alive():
        return
    with dummy_namespace.parent_pipe_lock:
        dummy_namespace.parent_pipe.send(None)
        dummy_namespace.child_process.join()
        dummy_namespace.parent_pipe.close()


def _child_loop(
    child_pipe,
    initializer,
    initargs,
    initkwargs,
    close_method_name,
    closeargs,
    closekwargs,
):
    """The event loop of a ObjectInSubprocess's child process

    Parameters
    ----------
    child_pipe : object
        multiprocessing.connection.Connection object.
    initializer :
        ...
    initargs : tuple
        e.g., (False, Namespace(verbose=False, synthetic_hardware=True, debug=False,
        CPU=True, config_file=None, experiment_file=None, etl_const_file=None,
        logging_config=None))
    initkwargs : dict
        e.g., {'configuration_path': PosixPath('.../config/configuration.yml'),
        'experiment_path':
        PosixPath('.../config/experiment.yml'),
        'waveform_constants_path': PosixPath('.../config/waveform_constants.yml'),
        'event_queue': <multiprocessing.queues.Queue object at 0x7fdd509c7c40>}
    close_method_name : NoneType
        None
    closeargs : NoneType
        None
    closekwargs : NoneType
        None

    """
    # Initialization.
    printed_output = io.StringIO()
    try:  # Create an instance of our object...
        with redirect_stdout(printed_output):
            obj = initializer(*initargs, **initkwargs)
            if close_method_name is not None:
                close_method = getattr(obj, close_method_name)
                closeargs = tuple() if closeargs is None else closeargs
                closekwargs = dict() if closekwargs is None else closekwargs
                atexit.register(lambda: close_method(*closeargs, **closekwargs))
                # Note: We don't know if print statements in the close method
                # will print in the main process.
        child_pipe.send(("Successfully initialized", printed_output.getvalue()))
    except Exception as e:  # If we fail to initialize, just give up.
        e.child_traceback_string = traceback.format_exc()
        child_pipe.send((e, printed_output.getvalue()))
        return None
    # Main loop:
    while True:
        printed_output = io.StringIO()
        try:
            cmd = child_pipe.recv()
        except EOFError:  # This implies the parent is dead; exit.
            return None
        if cmd is None:  # This is how the parent signals us to exit.
            return None
        method_name, args, kwargs = cmd
        try:
            with redirect_stdout(printed_output):
                result = getattr(obj, method_name)(*args, **kwargs)
            if callable(result):
                result = _dummy_function  # Cheaper than sending a real callable
            child_pipe.send((result, printed_output.getvalue()))
        except Exception as e:
            # e.child_traceback_string = traceback.format_exc()
            print("Exception inside ObjectInSubprocess:", traceback.format_exc())
            child_pipe.send((Exception(str(e)), printed_output.getvalue()))


# A minimal class that we use just to get another namespace:


class _DummyClass:
    pass


# If we're trying to return a (presumably worthless) "callable" to
# the parent, it might as well be small and simple:


def _dummy_function():
    return None


class _WaitingList:
    """For synchronization of one-thread-at-a-time shared resources

    Each ObjectInSubprocess has a _WaitingList; if you want to define your own
    _WaitingList-like objects that can interact with
    _Custody.switch_from() and _Custody._wait_in_line(), make sure they have
    a waiting_list = [] attribute, and a waiting_list_lock =
    threading.Lock() attribute.
    """

    def __init__(self):
        self.waiting_list = []  # Switch to a queue/deque if speed really matters
        self.waiting_list_lock = threading.Lock()

    def __enter__(self):
        self.waiting_list_lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.waiting_list_lock.release()


class _ObjectInSubprocessPipeLock:
    """Raises an educational exception (rather than blocking) when you try
    to acquire a locked lock.
    """

    def __init__(self):
        self.lock = threading.Lock()

    def __enter__(self):
        if not self.lock.acquire(blocking=False):
            raise RuntimeError(
                "Two different threads tried to use the same "
                "ObjectInSubprocess at the same time! This is bad. Look at the "
                "docstring of concurrency_tools.py to see an example of how "
                "to use a _Custody object to avoid this problem."
            )
        return self.lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()


threading_lock_type = type(threading.Lock())  # Used for typechecking


def _get_list_and_lock(resource):
    """Convenience function.

    Expected input: An ObjectInSubprocess, a _WaitingList, or a
    _WaitingList-like object with 'waiting_list' and
    'waiting_list_lock' attributes.
    """
    if isinstance(resource, ObjectInSubprocess):
        waiting_list = resource._.waiting_list.waiting_list
        waiting_list_lock = resource._.waiting_list.waiting_list_lock
    else:  # Either a _WaitingList, or a good enough impression
        waiting_list = resource.waiting_list
        waiting_list_lock = resource.waiting_list_lock
    assert isinstance(waiting_list_lock, threading_lock_type)
    return waiting_list, waiting_list_lock


class _Custody:
    def __init__(self):
        """For synchronization of single-thread-at-a-time shared resources.

        See the docstring at the start of this module for example usage.
        For _Custody() to be useful, at least some of the objects
        accessed by your launched thread must be ObjectInSubprocess()s,
        _WaitingList()s, or _WaitingList-like objects.
        """
        self.permission_slip = threading.Lock()
        self.permission_slip.acquire()
        self.has_custody = False
        self.target_resource = None

    def switch_from(self, resource, to=None, wait=True):
        """Get in line for a shared resource, then abandon your current resource

        If wait==True, also wait in that line until it's your turn to
        own the next shared resource.
        """
        assert resource is not None or to is not None
        if to is not None:
            to_waiting_list, to_waiting_list_lock = _get_list_and_lock(to)
            with to_waiting_list_lock:  # Get in the line for the next lock...
                if self not in to_waiting_list:  # ...unless you're already in it
                    to_waiting_list.append(self)
        if resource is not None:
            assert self.has_custody
            waiting_list, waiting_list_lock = _get_list_and_lock(resource)
            with waiting_list_lock:
                waiting_list.pop(0)  # Remove ourselves from the current line
                if len(waiting_list) > 0:  # If anyone's next...
                    # ...wake them up
                    waiting_list[0].permission_slip.release()
        self.has_custody = False
        self.target_resource = to
        if wait and self.target_resource is not None:
            self._wait_in_line()

    def release(self):
        """Release custody of the current shared resource.

        If you get custody of a shared resource and then raise an exception,
        the next-in-line might wait forever.

        'release' is useful while handling exceptions, if you want to pass
        custody of the resource to the next-in-line.

        This only works if you currently have custody, but it's hard to raise
        an exception while waiting in line.
        """
        if self.has_custody:
            self.switch_from(self.target_resource, to=None)
        else:
            if self.target_resource is None:
                return
            waiting_list, waiting_list_lock = _get_list_and_lock(self.target_resource)
            with waiting_list_lock:
                waiting_list.remove(self)

    def _wait_in_line(self):
        """Wait in line until it's your turn."""
        waiting_list, _ = _get_list_and_lock(self.target_resource)
        if self.has_custody:
            assert self is waiting_list[0]
            return
        # Wait for your number to be called
        if self is waiting_list[0] and self.permission_slip.locked():
            self.permission_slip.release()  # We arrived to an empty waiting list
        self.permission_slip.acquire()  # Blocks if we're not first in line
        self.has_custody = True


# When an exception from a child process isn't handled by the parent
# process, we'd like the parent to print the child traceback. Overriding
# sys.excepthook and threading.excepthook seems to be the standard way
# to do this:


def _try_to_print_child_traceback(v):
    if hasattr(v, "child_traceback_string"):
        print(
            f'{" Child Process Traceback ":v^79s}\n',
            v.child_traceback_string,
            f'{" Child Process Traceback ":^^79s}\n',
            f'{" Main Process Traceback ":v^79s}',
        )


def _my_excepthook(t, v, tb):
    """Show a traceback when a child exception isn't handled by the parent."""
    _try_to_print_child_traceback(v)
    return sys.__excepthook__(t, v, tb)


sys.excepthook = _my_excepthook

# Multiprocessing code works fairly differently depending whether you
# use 'spawn' or 'fork'. Since 'spawn' seems to be available on every
# platform we care about, and 'fork' is either missing or broken on some
# platforms, we'll always use 'spawn'. If your code calls
# mp.set_start_method() and sets it to anything other than 'spawn', this
# will crash with a RuntimeError. If you really need 'fork', or
# 'forkserver', then you probably know what you're doing better than us,
# and you shouldn't be using this module.
if mp.get_start_method(allow_none=True) != "spawn":
    mp.set_start_method("spawn")
