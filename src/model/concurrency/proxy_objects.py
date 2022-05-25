# Multiprocessing to spread CPU load, threading for concurrency:
import logging
import multiprocessing as mp
import threading
# Printing from a child process is tricky:
import io
from contextlib import redirect_stdout
# Showing exceptions from a child process is tricky:
import sys
import traceback
# Making sure a child process closes when the parent exits is tricky:
import atexit
import signal
# Sharing memory between child processes is tricky:
import ctypes as C
from pathlib import Path
# Logger Setup
p = Path(__file__).resolve().parts[7]
logger = logging.getLogger(p)

try:
    import numpy as np
except ImportError:
    np = None

"""
Sometimes we put a computationally demanding Python object in a
multiprocessing child process, but this usually leads to high mental
overhead. Using pipes and queues for calling methods, getting/setting
attributes, printing, handling exceptions, and cleanup can lean to ugly
code and confusion. Can we isolate most of this mental overhead to this
module? If we do it right, we'll be able to write fairly sophisticated
code that's still fairly readable. Note that the following code is
effectively uncommented; can you still figure out what it's doing?

                ####################################################
                #  EXAMPLE CODE (copypaste into 'test.py' and run) #
                ####################################################
from proxy_objects import ProxyManager, launch_custody_thread
from dummy_module import Camera, Preprocessor, Display

def main():
    pm = ProxyManager(shared_memory_sizes=(10*2000*2000*2, # Two data buffers
                                           10*2000*2000*2,
                                            1*2000*2000*1, # Two display buffers
                                            1*2000*2000*1))
    data_buffers = [pm.shared_numpy_array(0, (10, 2000, 2000), 'uint16'),
                    pm.shared_numpy_array(1, (10, 2000, 2000), 'uint16')]
    display_buffers = [pm.shared_numpy_array(2, (2000, 2000), 'uint8'),
                       pm.shared_numpy_array(3, (2000, 2000), 'uint8')]

    camera = pm.proxy_object(Camera)
    preprocessor = pm.proxy_object(Preprocessor)
    display = pm.proxy_object(Display)

    def snap(data_buffer, display_buffer, custody):
        custody.switch_from(None, to=camera)
        camera.record(out=data_buffer)

        custody.switch_from(camera, to=preprocessor)
        preprocessor.process(data_buffer, out=display_buffer)

        custody.switch_from(preprocessor, to=display)
        display.show(display_buffer)

        custody.switch_from(display, to=None)

    for i in range(15):
        th0 = launch_custody_thread(target=snap, first_resource=camera,
                            args=(data_buffers[0], display_buffers[0]))
        if i > 0:
            th1.join()
        th1 = launch_custody_thread(target=snap, first_resource=camera,
                            args=(data_buffers[1], display_buffers[1]))
        th0.join()
    th1.join()

if __name__ == '__main__':
    main()
            #####################################################
            #  This code is imported by the example code above. #
            #       Copypaste it into 'dummy_module.py'         #
            #####################################################
class Camera:
    def record(self, out):
        out.fill(1)

class Preprocessor:
    def process(self, x, out):
        x.max(axis=0, out=out)

class Display:
    def show(self, image):
        pass
                            ######################
                            #  END EXAMPLE CODE  #
                            ######################

Notice how little attention this code is spending on the fact that the
instances of the Camera, Preprocessing, and Display objects actually
live in child processes, communicate over pipes, and synchronize access
to shared memory.

Note that the method calls to our proxied object still block the parent
process; the idea is, the parent process is now effectively IO-limited
rather than CPU-limited, so we can write clean(er)-looking threading
code in the parent if we want multiple things to happen at once in the
parent.

Also note that multiprocessing already has proxied objects via
"managers"; we're rolling our own to learn, and have complete control.
If at the end of the process, we don't like ours better, we'll switch to
multiprocessing proxies.

CURRENT LIMITATIONS:

Like all python code that relies on multiprocessing, if you use this
module, you have to protect the "entry point" of your program. The
typical way to do this is by using an "if __name__ == '__main__':" block:

import numpy as np
from proxy_objects import ProxyObject
from dummy_module import Display

def main():
    disp = ProxyObject(Display)
    image = np.random.random((2000 2000))
    disp.show(image)

if __name__ == '__main__':
    main()
"""


class ProxyManager:
    """Allocates shared memory and spawns proxy objects

    If you want your ProxyObjects to share memory with the parent
    process (and each other), allocate a ProxyManager first, and use it
    to spawn your ProxyObjects.
    """

    def __init__(self, shared_memory_sizes=tuple()):
        """Allocate shared memory as multiprocessing Arrays.
        """
        if np is None:
            raise ImportError("We failed to import Numpy," +
                              " so there's no point using a ProxyManager.")
        self.shared_mp_arrays = tuple(mp.Array(C.c_uint8, sz)
                                      for sz in shared_memory_sizes)

    def proxy_object(
        self,
        initializer,
        *initargs,
        custom_loop=None,
        **initkwargs
    ):
        """Spawn a ProxyObject that has access to shared memory.
        """
        return ProxyObject(initializer, *initargs, **initkwargs,
                           custom_loop=custom_loop,
                           shared_mp_arrays=self.shared_mp_arrays)

    def shared_numpy_array(self, which_mp_array, shape, dtype=np.uint8):
        """View some of our shared memory as a numpy array.

        You can pass these shared numpy arrays to and from ProxyObjects
        without (slow) serialization.
        """
        assert which_mp_array in range(len(self.shared_mp_arrays))
        return _SharedNumpyArray(arrays=self.shared_mp_arrays, shape=shape,
                                 dtype=dtype, buffer=which_mp_array)


class ProxyObject:
    def __init__(
        self,
        initializer,
        *initargs,
        shared_mp_arrays=tuple(),
        custom_loop=None,
        close_method_name=None,
        closeargs=None,
        closekwargs=None,
        **initkwargs,
    ):
        """Make an object in a child process, that acts like it isn't.

        As much as possible, we try to make instances of ProxyObject
        behave as if they're an instance of the proxied object living in
        the parent process. They're not, of course: they live in a child
        process. If you have spare cores on your machine, this turns
        CPU-bound operations into IO-bound operations, without too much
        mental overhead for the coder.

        initializer -- callable that returns an instance of a Python object.
        initargs, initkwargs --  Arguments to 'initializer'
        shared_mp_arrays -- Used by a ProxyManager to pass in shared memory.
        """
        # Put an instance of the Python object returned by 'initializer'
        # in a child process:
        initargs, initkwargs = _disconnect_shared_arrays(initargs, initkwargs)
        parent_pipe, child_pipe = mp.Pipe()
        child_loop = _child_loop if custom_loop is None else custom_loop
        child_process = mp.Process(
            target=child_loop,
            name=initializer.__name__,
            args=(child_pipe, shared_mp_arrays,
                  initializer, initargs, initkwargs,
                  close_method_name, closeargs, closekwargs))
        # Attribute-setting looks weird here because we override
        # __setattr__, and because we use a dummy object's namespace to
        # hold our attributes so we shadow as little of the proxied
        # object's namespace as possible:
        super().__setattr__('_', _DummyClass())  # Weird, but for a reason.
        self._.parent_pipe = parent_pipe
        self._.parent_pipe_lock = _ProxyObjectPipeLock()
        self._.child_pipe = child_pipe
        self._.child_process = child_process
        self._.shared_mp_arrays = shared_mp_arrays
        self._.waiting_list = _WaitingList()
        # Make sure the child process initialized successfully:
        with self._.parent_pipe_lock:
            self._.child_process.start()
            assert _get_response(self) == 'Successfully initialized'
        # Try to ensure the child process closes when we exit:
        atexit.register(lambda: _close(self))
        try:
            signal.signal(signal.SIGTERM, lambda s, f: _close(self))
        except ValueError:  # We are probably starting from  a thread.
            pass  # Signal handling can only happen from main thread

    def __getattr__(self, name):
        """Access attributes of the child-process object in the parent process.

        As much as possible, we want attribute access and method calls
        to *seem* like they're happening in the parent process, if
        possible, even though they actually involve asking the child
        process over a pipe.
        """
        with self._.parent_pipe_lock:
            self._.parent_pipe.send(('__getattribute__', (name,), {}))
            attr = _get_response(self)
        if callable(attr):
            def attr(*args, **kwargs):
                args, kwargs = _disconnect_shared_arrays(args, kwargs)
                with self._.parent_pipe_lock:
                    self._.parent_pipe.send((name, args, kwargs))
                    return _get_response(self)
        return attr

    def __setattr__(self, name, value):
        if isinstance(value, _SharedNumpyArray):
            value = value._disconnect()
        with self._.parent_pipe_lock:
            self._.parent_pipe.send(('__setattr__', (name, value), {}))
            return _get_response(self)


def _get_response(proxy_object):
    """Effectively a method of ProxyObject, but defined externally to
    minimize shadowing of the proxied object's namespace"""
    resp, printed_output = proxy_object._.parent_pipe.recv()
    if len(printed_output) > 0:
        print(printed_output, end='')
    if isinstance(resp, Exception):
        raise resp
    if isinstance(resp, _SharedNumpyArrayStub):
        resp = resp._reconnect(proxy_object._.shared_mp_arrays)
    return resp


def _close(proxy_object):
    """Effectively a method of ProxyObject, but defined externally to
    minimize shadowing of the proxied object's namespace"""
    if not proxy_object._.child_process.is_alive():
        return
    with proxy_object._.parent_pipe_lock:
        proxy_object._.parent_pipe.send(None)
        proxy_object._.child_process.join()


def _child_loop(child_pipe, shared_arrays,
                initializer, initargs, initkwargs,
                close_method_name, closeargs, closekwargs):
    """The event loop of a ProxyObject's child process
    """
    # If any of the input arguments are _SharedNumpyArrays, we have to
    # show them where to find shared memory:
    initargs, initkwargs = _reconnect_shared_arrays(initargs, initkwargs,
                                                    shared_arrays)
    # Initialization.
    printed_output = io.StringIO()
    try:  # Create an instance of our object...
        with redirect_stdout(printed_output):
            obj = initializer(*initargs, **initkwargs)
            # TODO default to "close" if it exists?
            if close_method_name is not None:
                close_method = getattr(obj, close_method_name)
                closeargs = tuple() if closeargs is None else closeargs
                closekwargs = dict() if closekwargs is None else closekwargs
                atexit.register(
                    lambda: close_method(
                        *closeargs, **closekwargs))
                # TODO - what happens to print statements? Are they guaranteed
                # to print in the main process?
        child_pipe.send(
            ('Successfully initialized',
             printed_output.getvalue()))
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
        attr_name, args, kwargs = cmd
        args, kwargs = _reconnect_shared_arrays(args, kwargs, shared_arrays)
        try:
            with redirect_stdout(printed_output):
                result = getattr(obj, attr_name)(*args, **kwargs)
            if callable(result):
                result = _dummy_function  # Cheaper than sending a real callable
            if isinstance(result, _SharedNumpyArray):
                result = result._disconnect()
            child_pipe.send((result, printed_output.getvalue()))
        except Exception as e:
            e.child_traceback_string = traceback.format_exc()
            child_pipe.send((e, printed_output.getvalue()))

# A minimal class that we use just to get another namespace:


class _DummyClass:
    pass

# If we're trying to return a (presumably worthless) "callable" to
# the parent, it might as well be small and simple:


def _dummy_function():
    return None


class _WaitingList:
    """For synchronization of one-thread-at-a-time shared resources

    Each ProxyObject has a _WaitingList; if you want to define your own
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


class _ProxyObjectPipeLock:
    '''Raises an educational exception (rather than blocking) when you try
       to acquire a locked lock.'''

    def __init__(self):
        self.lock = threading.Lock()

    def __enter__(self):
        if not self.lock.acquire(blocking=False):
            raise RuntimeError(
                "Two different threads tried to use the same ProxyObject " +
                "at the same time! This is bad. Look at the docstring of " +
                "proxy_objects.py to see an example of how to use a _Custody " +
                "object to avoid this problem.")
        return self.lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()


threading_lock_type = type(threading.Lock())  # Used for typechecking


def _get_list_and_lock(resource):
    """Convenience function.

    Expected input: A ProxyObject, a _WaitingList, or a
    _WaitingList-like object with 'waiting_list' and
    'waiting_list_lock' attributes.
    """
    if isinstance(resource, ProxyObject):
        waiting_list = resource._.waiting_list.waiting_list
        waiting_list_lock = resource._.waiting_list.waiting_list_lock
    else:  # Either a _WaitingList, or a good enough impression
        waiting_list = resource.waiting_list
        waiting_list_lock = resource.waiting_list_lock
    assert isinstance(waiting_list_lock, threading_lock_type)
    return waiting_list, waiting_list_lock


def launch_custody_thread(target, first_resource=None, args=(), kwargs=None):
    """A thin wrapper around threading.Thread(), useful for ProxyObjects

    Along with ProxyManager (and maybe ProxyObject), this is one of the
    few definitions from this module you should call directly. See the
    docstring at the top of this module for an example of usage.

    The 'target' function must accept a 'custody' keyword argument (an
    instance of _Custody()), which will be used to call
    'custody.switch_from()' (and 'custody._wait_in_line()').

    'first_resource' is an instance of ProxyObject, _WaitingList,
    or a _WaitingList-like object. The 'target' function is
    expected to call custody.switch_from(None, first_resource) almost
    immediately (waiting in line until the shared resource is available).
    """
    if kwargs is None:
        kwargs = {}
    custody = _Custody()  # Useful for synchronization in the launched thread
    if first_resource is not None:
        # Get in line for custody of the first resource the launched
        # thread will use, but don't *wait* in that line; the launched
        # thread should do the waiting, not the main thread:
        custody.switch_from(None, first_resource, wait=False)
    kwargs['custody'] = custody
    thread = launch_thread(target, args, kwargs)
    thread.custody = custody
    return thread


def launch_thread(target, args=(), kwargs=None):
    """A thin wrapper around thread.Thread(), useful for ProxyObjects.

    Along with ProxyManager (and maybe ProxyObject), this is one of the
    few definitions from this module you should call directly. See the
    docstring at the top of this module for an example of usage.

    If your thread will acquire/release custody of a ProxyObject, use
    `launch_custody_thread` instead. Use this function to create a thread
    (instead of threading.Thread) when you feel like you need to launch another
    thread within a custody thread.

    The main purpose of this thread is so that the resulting thread can raise an
    exception when 'join' is called to detect if an error occoured in the
    threaded process.
    """
    if kwargs is None:
        kwargs = {}
    thread = _RaiseOnJoinThread(target=target, args=args, kwargs=kwargs)
    try:
        thread.start()
    except RuntimeError as e:
        if e.args == ("can't start new thread",):
            print('*' * 80)
            print('Failed to launch a custody thread.')
            print(threading.active_count(), 'threads are currently active.')
            print('You might have reached a limit of your system;')
            print('let some of your threads finish before launching more.')
            print('*' * 80)
        raise
    return thread


class _Custody:
    def __init__(self):
        """For synchronization of single-thread-at-a-time shared resources.

        See the docstring at the start of this module for example usage.
        For _Custody() to be useful, at least some of the objects
        accessed by your launched thread must be ProxyObject()s,
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
        """ Release custody of the current shared resource.

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
            waiting_list, waiting_list_lock = _get_list_and_lock(resource)
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


class _SharedNumpyArray(np.ndarray):
    """A numpy array that lives in shared memory

    In general, don't create these directly, create _SharedNumpyArrays
    (and ProxyObjects that use them) through calls to an instance of
    ProxyManager.

    Inputs and outputs to/from proxied objects are 'serialized', which
    is pretty fast - except for large in-memory objects. The only large
    in-memory objects we regularly deal with are numpy arrays, so it
    makes sense to provide a way to pass large numpy arrays to and from
    proxied objects via shared memory (which avoids slow serialization).

    There's a straightforward recipe to do this: declare an mp.Array in
    the parent process, pass it to the initializer of the child process,
    and view it as a numpy array with np.frombuffer in both parent and
    child. This works great, but breaks our ability to treat proxied
    objects as if they are in the parent process, and the resulting code
    can get pretty crazy looking.

    _SharedNumpyArray is a compromise: maybe you wanted to write code that
    looks like this:

        data_buf = np.zeros((400, 2000, 2000), dtype='uint16')
        display_buf = np.zeros((2000, 2000), dtype='uint8')

        camera = Camera()
        preprocessor = Preprocessor()
        display = Display()

        camera.record(num_images=400, out=data_buf)
        preprocessor.process(in=data_buf, out=display_buf)
        display.show(display_buf)

    ...but instead you write code that looks like this:

        pm = ProxyManager(shared_memory_sizes=(400*2000*2000*2, 2000*2000))
        data_buf = pm.shared_numpy_array(0, (400, 2000, 2000), dtype='uint16')
        display_buf = pm.shared_numpy_array(1, (2000, 2000), dtype='uint8')

        camera = pm.proxy_object(Camera)
        preprocessor = pm.proxy_object(Preprocessor)
        display = pm.proxy_object(Display)

        camera.record(num_images=400, out=data_buf)
        preprocessor.process(in=data_buf, out=display_buf)
        display.show(display_buf)

    ...and your payoff is, each object gets its own CPU core, AND passing
    large numpy arrays between the processes is still really fast!
    """
    def __new__(cls, arrays, shape=None, dtype=float, buffer=None, offset=0,
                strides=None, order=None):
        dtype = np.dtype(dtype)
        assert buffer in range(len(arrays)), f'Invalid buffer: <{buffer}>'
        requested_bytes = np.prod(shape, dtype='uint64') * dtype.itemsize
        if requested_bytes > len(arrays[buffer]):
            raise ValueError("Multiprocessing shared memory array is too " +
                             "small to hold the requested Numpy array.\n " +
                             f"{requested_bytes} > {len(arrays[buffer])}")
        obj = super(_SharedNumpyArray, cls).__new__(cls, shape, dtype,
                                                    arrays[buffer].get_obj(),
                                                    offset, strides, order)
        obj.buffer = buffer
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.offset = (
            self.__array_interface__['data'][0] -
            obj.__array_interface__['data'][0])
        self.buffer = getattr(obj, 'buffer', None)

    def _disconnect(self):
        """Return a tiny object describing ourselves

        You can pass this 'stub' down a pipe to a different process,
        giving it enough information to cheaply re-create an equivalent
        _SharedNumpyArray viewing the same shared memory.
        """
        return _SharedNumpyArrayStub(shape=self.shape, dtype=self.dtype,
                                     buffer=self.buffer,
                                     offset=getattr(self, 'offset', 0),
                                     strides=self.strides,
                                     order=None)


class _SharedNumpyArrayStub():
    """Suitable for cheaply passing through pipes to other processes"""

    def __init__(self, shape=None, dtype=float, buffer=None, offset=0,
                 strides=None, order=None):
        if shape is None:
            raise TypeError("Missing required argument 'shape'.")
        if buffer is None:
            raise TypeError("Missing required argument 'buffer'.")
        self.shape = shape
        self.dtype = dtype
        self.buffer = buffer
        self.offset = offset
        self.strides = strides
        self.order = order

    def _reconnect(self, arrays):
        """Reconstruct a 'full' version from this stub.
        """
        return _SharedNumpyArray(arrays, self.shape, self.dtype, self.buffer,
                                 self.offset, self.strides, self.order)


def _disconnect_shared_arrays(args, kwargs):
    """Replaces _SharedNumpyArrays in 'args' and 'kwargs' with new stubs
    """
    args = tuple(a._disconnect()
                 if isinstance(a, _SharedNumpyArray) else a
                 for a in args)
    kwargs = {k: v._disconnect()
              if isinstance(v, _SharedNumpyArray) else v
              for k, v in kwargs.items()}
    return args, kwargs


def _reconnect_shared_arrays(args, kwargs, shared_arrays):
    """Replaces stubs in 'args' and 'kwargs' with new _SharedNumpyArrays
    """
    args = tuple(a._reconnect(shared_arrays)
                 if isinstance(a, _SharedNumpyArrayStub) else a
                 for a in args)
    kwargs = {k: v._reconnect(shared_arrays)
              if isinstance(v, _SharedNumpyArrayStub) else v
              for k, v in kwargs.items()}
    return args, kwargs

# When an exception from a child process isn't handled by the parent
# process, we'd like the parent to print the child traceback. Overriding
# sys.excepthook and threading.excepthook seems to be the standard way
# to do this:


def _try_to_print_child_traceback(v):
    if hasattr(v, 'child_traceback_string'):
        print(f'{" Child Process Traceback ":v^79s}\n',
              v.child_traceback_string,
              f'{" Child Process Traceback ":^^79s}\n',
              f'{" Main Process Traceback ":v^79s}')


def _my_excepthook(t, v, tb):
    """Show a traceback when a child exception isn't handled by the parent.
    """
    _try_to_print_child_traceback(v)
    return sys.__excepthook__(t, v, tb)


sys.excepthook = _my_excepthook


class _RaiseOnJoinThread(threading.Thread):
    def join(self):
        super().join()
        if hasattr(self, 'exc_value'):
            raise self.exc_value


_original_threading_excepthook = threading.excepthook


def _my_threading_excepthook(args):
    """Show a traceback when a child exception isn't handled by the parent.
    """
    if isinstance(args.thread, _RaiseOnJoinThread):
        args.thread.exc_value = args.exc_value
        args.thread.exc_traceback = args.exc_traceback
        args.thread.exc_type = args.exc_type
    else:
        _try_to_print_child_traceback(args.exc_value)
    return _original_threading_excepthook(args)


threading.excepthook = _my_threading_excepthook

# Multiprocessing code works fairly differently depending whether you
# use 'spawn' or 'fork'. Since 'spawn' seems to be available on every
# platform we care about, and 'fork' is either missing or broken on some
# platforms, we'll always use 'spawn'. If your code calls
# mp.set_start_method() and sets it to anything other than 'spawn', this
# will crash with a RuntimeError. If you really need 'fork', or
# 'forkserver', then you probably know what you're doing better than us,
# and you shouldn't be using this module.
if mp.get_start_method(allow_none=True) != 'spawn':
    mp.set_start_method('spawn')

# Testing block.


class _Tests():
    '''
    Method names that start with `test_` will be run.

    Use: _test_... method names for tests that are called as part
    of a larger group.
    '''
    class TestClass:
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            for i, a in enumerate(args):
                setattr(self, f'arg_{i}', a)

        def printing_method(self, *args, **kwargs):
            print(*args, **kwargs)

        def printing_method2(self):
            print('Hello world 2', end='', flush=False)
            print(end='', flush=True)

        def test_method(self, *args, **kwargs):
            return (args, kwargs)

        def test_shared_numpy_input(self, shared_numpy_array):
            return shared_numpy_array.shape

        def test_shared_numpy_return(self, shape=(5, 5)):
            return _SharedNumpyArray(shape=shape)

        def test_modify_array(self, a):
            a.fill(1)
            return a

        def test_return_array(self, a):
            return a

        def nested_method(self, crash=False):
            self._nested_method(crash)

        def _nested_method(self, crash):
            if crash:
                raise ValueError('This error was supposed to be raised')

    def __init__(self):
        print(f'{"#":#^80s}')
        print(f'{" Running Tests ":#^80s}')
        print(f'{"#":#^80s}')
        self.tests = 0
        self.passed = 0

    def test_create_proxy_manager(self):
        pm = ProxyManager((100, 100))

    def test_create_proxy_object(self):
        pm = ProxyManager((100, 100))
        proxy_obj = pm.proxy_object(_Tests.TestClass)

    def test_reconnnecting_and_disconnecting_views(self):
        pm = ProxyManager((int(1e9),))
        for i in range(1000):
            self._trial_slicing_of_shared_array(pm)

    def _trial_slicing_of_shared_array(self, pm):
        ri = np.random.randint  # Just to get short lines
        dtype = np.dtype(np.random.choice(
            [np.uint16, np.uint8, float, np.float32, np.float64]))
        original_dimensions = tuple(
            ri(2, 100) for d in range(ri(2, 5)))
        slicer = tuple(
            slice(
                ri(0, a // 2),
                ri(0, a // 2) * -1,
                ri(1, min(6, a))
            )
            for a in original_dimensions)
        a = pm.shared_numpy_array(0, shape=original_dimensions, dtype=dtype)
        a.fill(0)
        b = a[slicer]  # should be a view
        b.fill(1)
        expected_total = int(b.sum())
        reloaded_total = b._disconnect()._reconnect(pm.shared_mp_arrays).sum()
        assert expected_total == reloaded_total, \
            f'Failed {dtype.name}/{original_dimensions}/{slicer}'

    def test_passing_normal_numpy_array(self):
        shape = (10, 10)
        dtype = int
        sz = int(np.prod(shape, dtype='uint64') * np.dtype(int).itemsize)
        pm = ProxyManager((sz, sz))
        a = np.zeros(shape, dtype)
        object_with_shared_memory = pm.proxy_object(_Tests.TestClass)
        object_with_shared_memory.test_shared_numpy_input(a)

    def test_passing_retrieving_shared_array(self):
        shape = (10, 10)
        dtype = int
        sz = int(np.prod(shape, dtype='uint64') * np.dtype(int).itemsize)
        pm = ProxyManager((sz, sz))
        object_with_shared_memory = pm.proxy_object(_Tests.TestClass)
        a = pm.shared_numpy_array(which_mp_array=0, shape=shape, dtype=dtype)
        a.fill(0)
        a = object_with_shared_memory.test_modify_array(a)
        assert a.sum() == np.product(shape, dtype='uint64'), (
            'Contents of array not correct!')

    def test_raise_attribute_error(self):
        a = ProxyObject(_Tests.TestClass, 'attribute', x=4,)
        try:
            a.z
        except AttributeError as e:  # Get __this__ specific error
            print("Attribute error handled by parent process:\n ", e)

    def test_printing_in_child_process(self):
        a = ProxyObject(_Tests.TestClass, 'attribute', x=4,)
        b = ProxyObject(_Tests.TestClass, x=5)
        b.printing_method('Hello')
        a.printing_method('A')
        a.printing_method('Hello', 'world', end='', flush=True)
        a.printing_method('')
        a.printing_method(a.x, '... ', end='', flush=False)
        b.printing_method(b.x)
        expected_output = 'Hello\nA\nHello world\n4 ... 5\n'
        return expected_output

    def test_setting_attribute_of_proxy(self):
        a = ProxyObject(_Tests.TestClass, 'attribute', x=4,)
        a.z = 10
        assert a.z == 10
        setattr(a, 'z', 100)
        assert a.z == 100

    def test_getting_attribute_of_proxy(self):
        a = ProxyObject(_Tests.TestClass, 'attribute', x=4)
        assert a.x == 4
        assert getattr(a, 'x') == 4

    def test_proxy_object_overhead(self):
        print('Performace summary:')
        n_loops = 10000
        a = ProxyObject(_Tests.TestClass, 'attribute', x=4,)
        t = self.time_it(
            n_loops, a.test_method, timeout_us=100, name='Trivial method call')
        print(f" {t:.2f} \u03BCs per trivial method call.")
        t = self.time_it(
            n_loops, lambda: a.x, timeout_us=100, name='Attribute access')
        print(f" {t:.2f} \u03BCs per get-attribute.")
        a.x = 4  # test set attribute with normal syntax
        t = self.time_it(n_loops, lambda: setattr(a, 'x', 5),
                         timeout_us=100, name='Attribute setting')
        print(f" {t:.2f} \u03BCs per set-attribute.")
        t = self.time_it(n_loops, lambda: a.z, fail=False, timeout_us=200,
                         name='Attribute error')
        print(f" {t:.2f} \u03BCs per parent-handled exception.")
        self._test_passing_array_performance()

    def _test_passing_array_performance(self):
        from itertools import product
        shape = (1000, 1000)
        dtype = np.uint8
        pass_methods = ['reference', 'serialization']
        method_names = ['test_shared_numpy_input', 'test_modify_array']
        shapes = [(10, 10), (1000, 1000)]
        for s, f, m in product(shapes, method_names, pass_methods):
            self._test_array_passing(m, f, s, dtype, 1000)

    def _test_array_passing(self, pass_by, method_name, shape, dtype, n_loops):
        dtype = np.dtype(dtype)
        sz = int(np.prod(shape, dtype='uint64') * np.dtype(int).itemsize)
        pm = ProxyManager((sz, sz))
        direction = '<->' if method_name == 'test_modify_array' else '->'
        name = f'{shape} array {direction} {pass_by}'
        object_with_shared_memory = pm.proxy_object(_Tests.TestClass)
        if pass_by == 'reference':
            a = pm.shared_numpy_array(0, shape, dtype=dtype)
            timeout_us = 5e3
        elif pass_by == 'serialization':
            a = np.zeros(shape=shape, dtype=dtype)
            timeout_us = 1e6
        func = getattr(object_with_shared_memory, method_name)
        t_per_loop = self.time_it(n_loops, func, (a,), timeout_us=timeout_us,
                                  name=name)
        print(f' {t_per_loop:.2f} \u03BCs per {name}')

    def test_lock_with_waitlist(self):
        import time
        try:
            from tqdm import tqdm
        except ImportError:
            tqdm = None  # No progress bars :(

        camera_lock = _WaitingList()
        display_lock = _WaitingList()

        def snap(i, custody):
            if tqdm is not None:
                pbars['camera'].update(1)
            if tqdm is not None:
                pbars['camera'].refresh()
            # We're already in line for the camera; wait until you're first in
            # line
            custody.switch_from(None, camera_lock)
            # Use the resource
            time.sleep(0.02)
            order['camera'].append(i)
            if tqdm is not None:
                pbars['camera'].update(-1)
            if tqdm is not None:
                pbars['display'].update(1)
            if tqdm is not None:
                pbars['camera'].refresh()
            if tqdm is not None:
                pbars['display'].refresh()
            custody.switch_from(camera_lock, display_lock)
            # Use the resource
            time.sleep(0.05)
            order['display'].append(i)
            # Move to the next resource
            custody.switch_from(display_lock, None)
            if tqdm is not None:
                pbars['display'].update(-1)
            if tqdm is not None:
                pbars['display'].refresh()
            return None

        num_snaps = 100
        order = {'camera': [], 'display': []}
        if tqdm is not None:
            f = '{desc: <30}{n: 3d}-{bar:45}|'
            pbars = {n: tqdm(total=num_snaps, unit='th',
                             bar_format=f, desc=f'Threads waiting on {n}')
                     for n in order.keys()}
        threads = []
        for i in range(num_snaps):
            threads.append(launch_custody_thread(snap, camera_lock, args=(i,)))
        for th in threads:
            th.join()

        if tqdm is not None:
            for pb in pbars.values():
                pb.close()

        assert order['camera'] == list(range(num_snaps))
        assert order['display'] == list(range(num_snaps))

    def test_incorrect_thread_management(self):

        p = ProxyObject(_Tests.TestClass)
        p.x = 5
        exceptions = [1]

        def t():
            try:
                p.x
            except RuntimeError:  # Should raise this
                pass
            else:
                exceptions.append(1)
        for i in range(100):
            threading.Thread(target=t).start()
        if sum(exceptions) == 0:
            raise UserWarning('No exceptions raised.'
                              'Expected some RuntimeErrors')

    def test_proxy_with_lock_with_waitlist(self):
        import time
        try:
            from tqdm import tqdm
        except ImportError:
            tqdm = None  # No progress bars :(

        def snap(i, custody):
            prev_res = None
            itr = enumerate(zip(resources, res_names, funcs))
            for ri, (res, name, resource_funcs) in itr:
                if tqdm is not None:
                    pbars[name].update(1)  # Be careful to access the resource
                    pbars[name].refresh()  # before you have control of it.
                custody.switch_from(prev_res, res)
                for fname in resource_funcs:
                    a = getattr(res, fname)(i)
                results[i].append(a)
                acq_order[res.name].append(i)
                if tqdm is not None:
                    pbars[res.name].update(-1)
                    pbars[res.name].refresh()
                prev_res = res
            custody.switch_from(res, None)

        NUM_STEPS = 4  # matches the number of steps for check results.
        num_snaps = 30  # Number of threads to start

        # Create proxy objects of resources to use.
        # Each has a method that sleep for some ammount of time and
        # returns `True`.
        camera = ProxyObject(_DummyCamera, name='camera')
        processor = ProxyObject(_DummyProcessor, name='processor')
        display = ProxyObject(_DummyGUI, name='display')
        disk = ProxyObject(_DummyFileSaver, name='disk')
        resources = [camera, processor, display, disk]
        res_names = [str(r.name) for r in resources]
        acq_order = {r.name: [] for r in resources}
        results = [[] for i in range(num_snaps)]
        funcs = [('record',),  # methods to call for camera
                 ('process', ),  # methods to call for processor
                 ('display', ),  # methods to call for display
                 ('save', )  # methods to call for for disk.
                 ]
        if tqdm is not None:
            f = '{desc: <30}{n: 3d}-{bar:45}|'
            pbars = {n: tqdm(total=num_snaps, unit='th',
                             bar_format=f, desc=f'Threads waiting on {n}')
                     for n in acq_order.keys()}
        threads = []
        for i in range(num_snaps):
            threads.append(launch_custody_thread(snap, camera, args=(i,)))
        for th in threads:
            th.join()

        if tqdm is not None:
            for pb in pbars.values():
                pb.close()

        # Check results
        for i, a in enumerate(results):
            assert sum(a) == NUM_STEPS * i, f'{i}-{a}'
        for r, th_o in acq_order.items():
            assert sorted(th_o) == th_o,\
                f'Resource `{r}` was used out of order! -- {th_o}'

    def run(self, test_prefix='test_'):
        tests = [i for i in dir(self) if i.startswith(test_prefix)]
        self.tests = len(tests)
        for i, t in enumerate(tests):
            self._run_single_test(i, t)
        self._summarize_results()

    def _run_single_test(self, i, t):
        printed_output = io.StringIO()
        name = t[5:].replace('_', ' ')
        print(f'{f"     {i+1} of {self.tests} | Testing {name}    ":-^80s}')
        try:
            with redirect_stdout(printed_output):
                expected_output = getattr(self, t)()
            if expected_output is not None:
                o = printed_output.getvalue()
                assert expected_output == o, \
                    f'\n Returned result:\n'\
                    f'    `{repr(o)}`\n'\
                    f' Did not match expected output:\n'\
                    f'     "{repr(expected_output)}"\n'
        except Exception as e:
            print('v' * 80)
            print(traceback.format_exc().strip('\n'))
            print('^' * 80)
        else:
            self.passed += 1
            if printed_output.getvalue():
                for l in printed_output.getvalue().strip('\n').split('\n'):
                    print(f'   {l}')
            print(f'{f"> Success <":-^80s}')

    def _summarize_results(self):
        fill = '#' if self.passed == self.tests else '!'
        print(f'{fill}' * 80)
        message = f"Completed Tests -- passed {self.passed} of {self.tests}"
        if fill == "#":
            print(f'{f"  {message}  ":#^80s}')
        else:
            print(f'{f"  {message}  ":!^80s}')
        print(f'{fill}' * 80)

    def time_it(self, n_loops, func, args=None, kwargs=None, fail=True,
                timeout_us=None, name=None):
        import time
        try:
            from tqdm import tqdm
        except ImportError:
            tqdm = None  # No progress bars :(

        start = time.perf_counter()
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        if tqdm is not None:
            f = '{desc: <38}{n: 7d}-{bar:17}|[{rate_fmt}]'
            pb = tqdm(total=n_loops, desc=name, bar_format=f)
        for i in range(n_loops):
            if tqdm is not None:
                pb.update(1)
            try:
                func(*args, **kwargs)
            except Exception as e:
                if fail:
                    raise e
                else:
                    pass
        if tqdm is not None:
            pb.close()
        end = time.perf_counter()
        time_per_loop_us = ((end - start) / n_loops) * 1e6

        if timeout_us is not None:
            if time_per_loop_us > timeout_us:
                name = func.__name__ if name is None else name
                raise TimeoutError(
                    f'Timed out on {name}\n'
                    f'   args:{args}\n'
                    f'   kwargs: {kwargs}\n'
                    f' Each loop took {time_per_loop_us:.2f} \u03BCs'
                    f' (Allowed: {timeout_us:.2f} \u03BCs)')
        return time_per_loop_us

# TODO: Remove these if I can....


class _DummyObject:
    def __init__(self, name='generic_dummy_obj'):
        self.name = name


class _DummyCamera(_DummyObject):
    def record(self, a):
        import time
        time.sleep(.05)
        return a


class _DummyProcessor(_DummyObject):
    def process(self, a):
        import time
        time.sleep(.2)
        return a


class _DummyGUI(_DummyObject):
    def display(self, a):
        import time
        time.sleep(.002)
        return a


class _DummyFileSaver(_DummyObject):
    def save(self, a):
        import time
        time.sleep(.3)
        return a


if __name__ == '__main__':
    test_prefix = 'test_proxy_with_lock_with_waitlist'
    _Tests().run('test_')
