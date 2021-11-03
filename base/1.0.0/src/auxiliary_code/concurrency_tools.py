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
# Sharing memory between child processes is tricky:
try:
    from multiprocessing import shared_memory
    import numpy as np
except ImportError:
    shared_memory = None
    np = None

'''
Sometimes we put a computationally demanding Python object in a
multiprocessing child process, but this usually leads to high mental
overhead. Using pipes and queues for calling methods, getting/setting
attributes, printing, handling exceptions, and cleanup can lead to ugly
code and confusion. Can we isolate most of this mental overhead to this
module? If we do it right, we'll be able to write fairly sophisticated
code that's still fairly readable. Note that the following code is
very poorly commented; can you still figure out what it's doing?

                ####################################################
                #  EXAMPLE CODE (copypaste into 'test.py' and run) #
                ####################################################
import numpy as np
from concurrency_tools import ObjectInSubprocess, CustodyThread, SharedNDArray

# Tune these values to get reliable operation on your machine:
fps =    500           # Camera frames per second
shape = (16, 512, 512) # Pixel dimensions of each data buffer
N =      10            # Number of data buffers to acquire
description = (
    "Record -> Deconvolve -> Display -> Detect motion -> Save\n" +
    "%d bursts of %d %dx%d frames at %d frames/second"%(N, *shape, fps))

def without_concurrency():
    # On my machine, this prints:
    # Camera spends 322 ms working, but also spends 2644 ms waiting!
    ####################################################################
    print("Simulating acquiring without concurrency...\n" + description)
    ####################################################################
    camera =        Camera()
    preprocessor =  Preprocessor()
    display =       Display()
    postprocessor = Postprocessor()
    storage =       Storage()
    data_buffers = [np.zeros(shape, dtype='uint16') for x in range(N)]

    def timelapse(data_buffer):
        camera.record(data_buffer, fps)
        preprocessor.deconvolve(data_buffer)
        display.show(data_buffer)
        postprocessor.detect_motion(data_buffer)
        storage.save(data_buffer)

    for db in data_buffers:
        timelapse(db)
    print("Camera spends %0.0f ms working, but also spends %0.0f ms waiting!"%(
        camera.time_working*1000, camera.time_waiting*1000))

def with_concurrency():
    # On my machine, this prints:
    # Camera spends 323 ms working, but only spends 12 ms waiting.
    ####################################################################
    print("\nSimulating acquiring WITH concurrency...\n" + description)
    ####################################################################
    camera =        ObjectInSubprocess(Camera) # Can't tolerate threadswitching
    preprocessor =  ObjectInSubprocess(Preprocessor) # CPU-bound
    display =       ObjectInSubprocess(Display) # Slightly CPU-bound
    postprocessor = ObjectInSubprocess(Postprocessor) # CPU-bound
    storage =       Storage() # IO-bound, not CPU-bound
    data_buffers = [SharedNDArray(shape, dtype='uint16') for x in range(N)]

    def timelapse(data_buffer, custody):
        custody.switch_from(None, to=camera) # Wait in line to use the camera...
        camera.record(data_buffer, fps)
        custody.switch_from(camera, to=preprocessor) # Wait in the next line...
        preprocessor.deconvolve(data_buffer)
        custody.switch_from(preprocessor, to=display) # Wait in the next line...
        display.show(data_buffer)
        custody.switch_from(display, to=postprocessor) # Wait in the last line...
        postprocessor.detect_motion(data_buffer)
        custody.switch_from(postprocessor, to=None) # Use the disk immediately
        storage.save(data_buffer)

    threads = []
    for db in data_buffers:
        threads.append(CustodyThread( # This provides the "custody" object above
            first_resource=camera, target=timelapse, args=(db,)).start())
    for th in threads: # Wait for all our threads to finish
        th.get_result()
    print("Camera spends %0.0f ms working, but only spends %0.0f ms waiting."%(
        camera.time_working*1000, camera.time_waiting*1000))
    ####################################################################
    # We got huge performance gains using threads, subprocesses, and
    # shared memory. The code only got ~1.5x longer, and didn't get too
    # ugly! This is much nicer than everything else I've tried.
    ####################################################################

class Camera:
    def record(self, out, fps):
        """Reliable high-framerate recording doesn't tolerate any pauses"""
        import time
        dt = 1 / fps
        frames_dropped = 0
        start = time.perf_counter()
        for which_frame in range(out.shape[0]):
            t_frame_available = (1 + which_frame) * dt
            t_frame_dropped   = (3 + which_frame) * dt
            while time.perf_counter() - start < t_frame_available:
                pass # Simulate polling for the next frame
            if time.perf_counter() - start >= t_frame_dropped:
                frames_dropped += 1
            out[which_frame, 0::2, 1::2].fill(1) # Simulate copying a frame
            out[which_frame, 1::2, 0::2].fill(2)
        end = time.perf_counter()
        if frames_dropped > 0:
            print("Warning: the dummy camera dropped", frames_dropped, "frames")
        # Timing bookkeeping:
        if not hasattr(self, 'time_working'):
            self.time_working = 0
            self.time_waiting = 0
        if hasattr(self, 'last_end'):
            self.time_waiting += (start - self.last_end)
        self.time_working += (end - start)
        self.last_end = end

class Preprocessor:
    def deconvolve(self, x):
        """Live (mock) linear deconvolution is very CPU-hungry"""
        x_ft = np.fft.rfftn(x)
        fourier_mask = np.ones_like(x_ft) # Real decon mask would go here
        np.multiply(x_ft, fourier_mask, out=x_ft)
        x[:, :, :] = np.fft.irfftn(x_ft, s=x.shape)

class Display:
    def show(self, x):
        """Log-scale and normalize data, a little CPU-hungry"""
        im = np.log1p(x, dtype='float64')
        im -= im.min()
        if im.max() > 0:
            im /= im.max()

class Postprocessor:
    def detect_motion(self, x):
        """Motion detection is fairly CPU-hungry"""
        mean_img = np.median(x, axis=0)
        variance_img = np.var(x, axis=0)
        motion_map = np.zeros_like(mean_img)
        np.divide(variance_img, mean_img, out=motion_map, where=mean_img>10)
        if np.max(np.abs(motion_map)) > 5: # ~1 for Poisson data
            print("Motion detected!")

class Storage:
    def save(self, x):
        """Saving data to disk is IO-bound rather than CPU-bound"""
        from tempfile import TemporaryFile
        with TemporaryFile() as f:
            np.save(f, x)

if __name__ == '__main__':
    without_concurrency()
    with_concurrency()
                            ######################
                            #  END EXAMPLE CODE  #
                            ######################

Notice how little attention this code is spending on the fact that the
instances of the Camera, Preprocessing, Display, and Postprocessing objects
actually live in child processes, communicate over pipes, and synchronize access
to shared memory.

Note that the method calls to our objects-in-subprocesses still block the parent
process; the idea is, the parent process is now effectively IO-limited
rather than CPU-limited, so we can write clean(er)-looking threading
code in the parent if we want multiple things to happen at once in the
parent.

Also note that python's multiprocessing module already has
objects-in-subprocesses via "managers", called "proxy objects", and the Pyro
package (https://github.com/irmen/Pyro5) lets you "proxy" objects on different
machines. We're rolling our own to learn, and have complete control. If at the
end of the process, we don't like ours better, we'll switch to multiprocessing
proxies or Pyro.

CURRENT LIMITATIONS:

Like all python code that relies on multiprocessing, if you use this
module, you have to protect the "entry point" of your program. The
typical way to do this is by using an "if __name__ == '__main__':" block:

import numpy as np
from concurrency_tools import ObjectInSubprocess
from dummy_module import Display

def main():
    disp = ObjectInSubprocess(Display)
    image = np.random.random((2000 2000))
    disp.show(image)

if __name__ == '__main__':
    main()
'''

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
    def __new__(cls, shape=None, dtype=float, shared_memory_name=None,
                offset=0, strides=None, order=None):
        if shared_memory_name is None:
            dtype = np.dtype(dtype)
            requested_bytes = np.prod(shape, dtype='uint64') * dtype.itemsize
            requested_bytes = int(requested_bytes)
            try:
                shm = shared_memory.SharedMemory(
                    create=True, size=requested_bytes)
            except OSError as e:
                if e.args == (24, "Too many open files"):
                    raise OSError(
                        "You tried to simultaneously open more "
                        "SharedNDArrays than are allowed by your system!"
                    ) from e
                else:
                    raise e
            must_unlink = True # This process is responsible for unlinking
        else:
            shm = shared_memory.SharedMemory(
                name=shared_memory_name, create=False)
            must_unlink = False
        obj = super(SharedNDArray, cls).__new__(
            cls, shape, dtype, shm.buf, offset, strides, order)
        obj.shared_memory = shm
        obj.offset = offset
        if must_unlink:
            weakref.finalize(obj, shm.unlink)
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        if not isinstance(obj, SharedNDArray):
            raise ValueError(
                "You can't view non-shared memory as shared memory.")
        if hasattr(obj, "shared_memory") and  np.may_share_memory(self, obj):
            self.shared_memory = obj.shared_memory
            self.offset = obj.offset
            self.offset += (self.__array_interface__["data"][0] -
                             obj.__array_interface__["data"][0])

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
        args = (self.shape, self.dtype, self.shared_memory.name,
                self.offset, self.strides, None)
        return (SharedNDArray, args)

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
    def __init__(self, group=None, target=None, name=None, args=(),
                 kwargs=None):
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
                print("*"*80)
                print("Failed to launch a thread.")
                print(threading.active_count(), "threads are currently active.")
                print("You might have reached a limit of your system;")
                print("let some of your threads finish before launching more.")
                print("*"*80)
            raise
        return self

    def get_result(self, timeout=None):
        """Either returns a value or raises an exception.

        Optionally accepts a timeout in seconds. If thread has not returned
        after timeout seconds, raises a TimeoutError.
        """
        super().join(timeout=timeout)
        if self.is_alive(): ## Thread could potentially not be done yet!
            return TimeoutError('Thread did not return!')
        if hasattr(self, 'exc_value'):
            raise self.exc_value
        return self._return

class CustodyThread(ResultThread):
    """Threads that can access shared resources in the order they were launched.

    See the docstring at the top of this module for examples.
    """
    def __init__(self, first_resource=None,
                 group=None, target=None, name=None, args=(), kwargs=None):
        if "custody" not in inspect.signature(target).parameters:
            raise ValueError("The function 'target' passed to a CustodyThread"
            " must accept an argument named 'custody'")
        custody = _Custody() # Useful for synchronization in the launched thread
        if first_resource is not None:
            # Get in line for custody of the first resource the launched
            # thread will use, but don't *wait* in that line; the launched
            # thread should do the waiting, not the main thread:
            custody.switch_from(None, first_resource, wait=False)
        if kwargs is None: kwargs = {}
        if "custody" in kwargs:
            raise ValueError(
                "CustodyThread will create and pass a keyword argument to"
                " 'target' named 'custody', so keyword arguments to a"
                " CustodyThread can't be named 'custody'")
        kwargs["custody"] = custody
        super().__init__(group, target, name, args, kwargs)
        self.custody = custody

_original_threading_excepthook = threading.excepthook

def _my_threading_excepthook(args):
    """Show a traceback when a child exception isn't handled by the parent.
    """
    if isinstance(args.thread, ResultThread):
        args.thread.exc_value = args.exc_value
        args.thread.exc_traceback = args.exc_traceback
        args.thread.exc_type = args.exc_type
    else:
        _try_to_print_child_traceback(args.exc_value)
    return _original_threading_excepthook(args)

threading.excepthook = _my_threading_excepthook

FancyThread = ResultThread # So Andy can refer to it like this.
PoliteThread = CustodyThread

class ObjectInSubprocess:
    def __init__(self, initializer, *initargs, custom_loop=None,
                 close_method_name=None, closeargs=None, closekwargs=None,
                 **initkwargs):
        """Make an object in a child process, that acts like it isn't.

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
            args=(child_pipe, initializer, initargs, initkwargs,
                  close_method_name, closeargs, closekwargs))
        # Attribute-setting looks weird here because we override __setattr__,
        # and because we use a dummy object's namespace to hold our attributes
        # so we shadow as little of the object's namespace as possible:
        super().__setattr__("_", _DummyClass()) # Weird, but for a reason.
        self._.parent_pipe = parent_pipe
        self._.parent_pipe_lock = _ObjectInSubprocessPipeLock()
        self._.child_pipe = child_pipe
        self._.child_process = child_process
        self._.waiting_list = _WaitingList()
        # Make sure the child process initialized successfully:
        with self._.parent_pipe_lock:
            self._.child_process.start()
            assert _get_response(self) == "Successfully initialized"
        # Try to ensure the child process closes when we exit:
        dummy_namespace = getattr(self, "_")
        weakref.finalize(self, _close, dummy_namespace)
        try:
            signal.signal(signal.SIGTERM, lambda s, f: _close(dummy_namespace))
        except ValueError: # We are probably starting from a thread.
            pass # Signal handling can only happen from main thread

    def __getattr__(self, name):
        """Access attributes of the child-process object in the parent process.

        As much as possible, we want attribute access and method calls
        to *seem* like they're happening in the parent process, if
        possible, even though they actually involve asking the child
        process over a pipe.
        """
        with self._.parent_pipe_lock:
            self._.parent_pipe.send(("__getattribute__", (name,), {}))
            attr = _get_response(self)
        if callable(attr):
            def attr(*args, **kwargs):
                with self._.parent_pipe_lock:
                    self._.parent_pipe.send((name, args, kwargs))
                    return _get_response(self)
        return attr

    def __setattr__(self, name, value):
        with self._.parent_pipe_lock:
            self._.parent_pipe.send(("__setattr__", (name, value), {}))
            return _get_response(self)

def _get_response(object_in_subprocess):
    """Effectively a method of ObjectInSubprocess, but defined externally to
    minimize shadowing of the object's namespace
    """
    resp, printed_output = object_in_subprocess._.parent_pipe.recv()
    if len(printed_output) > 0:
        print(printed_output, end='')
    if isinstance(resp, Exception):
        raise resp
    return resp

def _close(dummy_namespace):
    """Effectively a method of ObjectInSubprocess, but defined externally to
    minimize shadowing of the object's namespace
    """
    if not dummy_namespace.child_process.is_alive():
        return
    with dummy_namespace.parent_pipe_lock:
        dummy_namespace.parent_pipe.send(None)
        dummy_namespace.child_process.join()
        dummy_namespace.parent_pipe.close()

def _child_loop(child_pipe, initializer, initargs, initkwargs,
                close_method_name, closeargs, closekwargs):
    """The event loop of a ObjectInSubprocess's child process"""
    # Initialization.
    printed_output = io.StringIO()
    try: # Create an instance of our object...
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
    except Exception as e: # If we fail to initialize, just give up.
        e.child_traceback_string = traceback.format_exc()
        child_pipe.send((e, printed_output.getvalue()))
        return None
    # Main loop:
    while True:
        printed_output = io.StringIO()
        try:
            cmd = child_pipe.recv()
        except EOFError: # This implies the parent is dead; exit.
            return None
        if cmd is None: # This is how the parent signals us to exit.
            return None
        method_name, args, kwargs = cmd
        try:
            with redirect_stdout(printed_output):
                result = getattr(obj, method_name)(*args, **kwargs)
            if callable(result):
                result = _dummy_function # Cheaper than sending a real callable
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

    Each ObjectInSubprocess has a _WaitingList; if you want to define your own
    _WaitingList-like objects that can interact with
    _Custody.switch_from() and _Custody._wait_in_line(), make sure they have
    a waiting_list = [] attribute, and a waiting_list_lock =
    threading.Lock() attribute.
    """
    def __init__(self):
        self.waiting_list = [] # Switch to a queue/deque if speed really matters
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
                "to use a _Custody object to avoid this problem.")
        return self.lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()

threading_lock_type = type(threading.Lock()) # Used for typechecking

def _get_list_and_lock(resource):
    """Convenience function.

    Expected input: An ObjectInSubprocess, a _WaitingList, or a
    _WaitingList-like object with 'waiting_list' and
    'waiting_list_lock' attributes.
    """
    if isinstance(resource, ObjectInSubprocess):
        waiting_list = resource._.waiting_list.waiting_list
        waiting_list_lock = resource._.waiting_list.waiting_list_lock
    else: # Either a _WaitingList, or a good enough impression
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
            with to_waiting_list_lock: # Get in the line for the next lock...
                if self not in to_waiting_list: # ...unless you're already in it
                    to_waiting_list.append(self)
        if resource is not None:
            assert self.has_custody
            waiting_list, waiting_list_lock = _get_list_and_lock(resource)
            with waiting_list_lock:
                waiting_list.pop(0) # Remove ourselves from the current line
                if len(waiting_list) > 0: # If anyone's next...
                    waiting_list[0].permission_slip.release() # ...wake them up
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
            self.permission_slip.release() # We arrived to an empty waiting list
        self.permission_slip.acquire() # Blocks if we're not first in line
        self.has_custody = True

# When an exception from a child process isn't handled by the parent
# process, we'd like the parent to print the child traceback. Overriding
# sys.excepthook and threading.excepthook seems to be the standard way
# to do this:
def _try_to_print_child_traceback(v):
    if hasattr(v, "child_traceback_string"):
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

# Testing block:
class MyTestClass:
    """Homemade testing class. Mostly written out of curiosity to see
    what features we would want and if it could be done easily without adding
    another import. Not as featured as a "real" testing package, but that
    wasn't the point.

    To create a set of tests, subclass this class and add methods to it.

    By default, methods names starting with `test_` will be called by `run`.

    If the test is expected to generate any specific print output in STDOUT,
    return that expected output as a string from the test function.
    """
    def run(self, test_prefix='test_', fail=False, fail_fast=False):
        """Runs all methods that begin with `test_prefix`"""
        tests = [i for i in dir(self) if i.startswith(test_prefix)]
        tests = [i for i in tests if callable(getattr(self, i))]

        print('#'*80)
        print(f'{f" Running Tests of {self.__class__.__name__} ":#^80s}')
        print('#'*80)
        self.num_tests = len(tests)
        self.num_passed = 0
        for i, t in enumerate(tests):
            passed = self._run_single_test(i, t)
            if fail_fast and not passed:
                raise RuntimeError("Failed!")
        passed_all = self._summarize_results()
        if fail and not passed_all:
            raise RuntimeError("Failed some of the tests!")

    def _run_single_test(self, i, t):
        printed_output = io.StringIO()
        name = t[5:].replace('_', ' ')
        print(f'{f"     {i+1} of {self.num_tests} | Testing {name}    ":-^80s}')
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
            print('v'*80)
            print(traceback.format_exc().strip('\n'))
            print('^'*80)
            print('v'*80)
            print(printed_output.getvalue())
            print('^'*80)
            return False
        else:
            self.num_passed += 1
            if printed_output.getvalue():
                for l in printed_output.getvalue().strip('\n').split('\n'):
                    print(f'   {l}')
            print(f'{f"> Success <":-^80s}')
            return True

    def _summarize_results(self):
        fill = '#' if self.num_passed == self.num_tests else '!'
        print(fill*80)
        message = (f"Completed Tests for {self.__class__.__name__} "
                   f"-- passed {self.num_passed} of {self.num_tests}")
        if self.num_passed == self.num_tests:
            print(f'{f"  {message}  ":#^80s}')
        else:
            print(f'{f"  {message}  ":!^80s}')
        print(fill*80)
        print()
        return self.num_passed == self.num_tests


    def time_it(self, n_loops, func, args=None, kwargs=None, fail=True,
                timeout_us=None, name=None):
        """Useful for testing the performance of a specific function.

        Args:
            - n_loops <int> | number of loops to test
            - func <callable> | function/method to test
            - args/kwargs | arguments to the function
            - fail <bool> | Allow the method to raise an exception?
            - timeout_us <int/float> | If the average duration exceeds this
                limit, raise a TimeoutError.
            - name <str> | formatted name for the progress bar.
        """
        import time
        try:
            from tqdm import tqdm
        except ImportError:
            tqdm = None # No progress bars :(
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        if tqdm is not None:
            f = '{desc: <38}{n: 7d}-{bar:17}|[{rate_fmt}]'
            pb = tqdm(total=n_loops, desc=name, bar_format=f)
        start = time.perf_counter()
        for i in range(n_loops):
            if tqdm is not None: pb.update(1)
            try:
                func(*args, **kwargs)
            except Exception as e:
                if fail:
                    raise e
                else:
                    pass
        end = time.perf_counter()
        if tqdm is not None: pb.close()
        time_per_loop_us = ((end-start) / n_loops)*1e6
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


class TestResultThreadAndCustodyThread(MyTestClass):
    """Various tests of the functions and expected behavior of the ResultThread
    and CustodyThread classes.
    """
    def test_subclassed_threading_types(self):
        r_th = ResultThread(target=lambda: 1)
        c_th = CustodyThread(target=lambda custody: 1)

        assert isinstance(r_th, threading.Thread)
        assert isinstance(c_th, threading.Thread)
        assert isinstance(r_th, ResultThread)
        assert isinstance(c_th, ResultThread)
        assert isinstance(c_th, CustodyThread)

    def test_threadlike_behavior(self):
        th = ResultThread(target=lambda: 1)
        th.start()
        th.join()
        assert not th.is_alive()

    def test_new_start_behavior(self):
        th = ResultThread(target=lambda: 1)
        _th = th.start()
        assert isinstance(_th, ResultThread)
        assert th is _th

    def test_getting_result(self):
        th = ResultThread(target=lambda: 1).start()
        assert hasattr(th, '_return')
        th.join()
        assert th.get_result() == 1
        assert th.get_result() == 1, "Couldn't get result twice!"

    def test_passing_args_and_kwargs(self):
        def mirror(*args, **kwargs):
            return args, kwargs
        a = (1,)
        k = dict(a=1)
        th = ResultThread(target=mirror, args=a, kwargs=k).start()
        _a, _k = th.get_result()
        assert a == _a, f"{a} != {_a}"
        assert k == _k, f"{k} != {_k}"

    def test_catching_exception(self):
        def e():
            raise ValueError("Don't worry, this exception occurred on purpose!")
        th = ResultThread(target=e).start()
        th.join() # join won't reraise exception in main thread
        assert hasattr(th, 'exc_value')
        try:
            th.get_result()
        except ValueError:
            pass
        else:
            raise AssertionError("We didn't get the exception we expected...")
        # We should be able to reraise this exception as long as we have
        # a reference to it:
        try:
            th.get_result()
        except ValueError:
            pass
        else:
            raise AssertionError("We didn't get the exception we expected...")

    def test_custody_thread_target_args(self):
        # CustodyThread accepts a target with a kwarg 'custody'
        def custody_f(custody=None):
            return 1
        th = CustodyThread(target=custody_f, first_resource=None).start()
        # CustodyThread accepts a target with a positional arg 'custody'
        def custody_f(custody):
            return 1
        th = CustodyThread(target=custody_f, first_resource=None).start()

        # CustodyThread will otherwise raise a ValueError
        def f():
            return 1
        try:
            th = CustodyThread(target=f, first_resource=None).start()
        except ValueError:
            pass # We expect this
        else:
            raise AssertionError("We didn't get the exception we expected...")
        def f(a):
            return 1
        try:
            th = CustodyThread(target=f, first_resource=None).start()
        except ValueError:
            pass # We expect this
        else:
            raise AssertionError("We didn't get the exception we expected...")
        def f(a=1):
            return 1
        try:
            th = CustodyThread(target=f, first_resource=None).start()
        except ValueError:
            pass # We expect this
        else:
            raise AssertionError("We didn't get the exception we expected...")

    def test_providing_first_resource(self):
        resource = _WaitingList()
        mutable_variables = {'step': 0, 'progress': 0}
        def f(custody):
            while mutable_variables['step'] == 0:
                pass
            custody.switch_from(None, resource)
            mutable_variables['progress'] += 1
            while mutable_variables['step'] == 1:
                pass
            custody.switch_from(resource, None)
            mutable_variables['progress'] += 1
            return
        try:
            th = CustodyThread(target=f, first_resource=resource).start()
            assert hasattr(th, "custody"), 'Should have a custody attribute.'
            assert not th.custody.has_custody, 'Should not have custody yet.'
            assert th.custody.target_resource is resource, 'Should be in line.'
            # Make target thread progress one step and acquire custody
            mutable_variables['step'] = 1
            while mutable_variables['progress'] == 0:
                pass # Wait for thread
            assert th.custody.has_custody, 'Should have gotten custody.'
            assert th.custody.target_resource is resource
            # Make target thread progress one step, release custody, and exit
            mutable_variables['step'] = 2
            while mutable_variables['progress'] == 1:
                pass # Wait for thread
            assert not th.custody.has_custody
            assert th.custody.target_resource is None
            th.join()
        finally: # if anything goes wrong, make sure the thread exits
            mutable_variables['step'] = -1

class TestSharedNDArray(MyTestClass):
    """Various tests of the SharedNDArray class"""
    def test_subclassed_numpy_array_types(self):
        a = SharedNDArray(shape=(1,), dtype='uint8')
        assert isinstance(a, SharedNDArray)
        assert isinstance(a, np.ndarray)
        assert type(a) is SharedNDArray, type(a)
        assert type(a) is not np.ndarray
        assert hasattr(a, "shared_memory")
        assert isinstance(a.shared_memory, shared_memory.SharedMemory)

    def test_ndarraylike_behavior(self):
        """Testing if we broke how an ndarray is supposed to behave."""
        ri = np.random.randint # Just to get short lines
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype='uint8')
        c = ri(0, 255, original_dimensions, dtype='uint8')
        a[:] = c # Fill 'a' with 'c's random values
        # A slice should still share memory
        view_by_slice = a[:1, 2:3, ..., :10, 100:-100]
        assert isinstance(a, SharedNDArray)
        assert type(a) is type(view_by_slice)
        assert np.may_share_memory(a, view_by_slice)
        assert a.shared_memory is view_by_slice.shared_memory

        # Some functions should not return a SharedNDArray
        b = a.sum(axis=-1)
        assert isinstance(b, np.ndarray), type(b)
        assert not isinstance(b, SharedNDArray)

        b = a + 1
        assert isinstance(b, np.ndarray), type(b)
        assert not isinstance(b, SharedNDArray), type(b)

        b = a.sum()
        assert np.isscalar(b)
        assert not isinstance(b, SharedNDArray)

    def test_serialization(self):
        """Testing serializing/deserializing a SharedNDArray"""
        import pickle
        ri = np.random.randint # Just to get short lines
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype='uint8')
        c = ri(0, 255, original_dimensions, dtype='uint8')
        a[:] = c # Fill 'a' with 'c's random values
        view_by_slice = a[:1, 2:3, ..., :10, 100:-100]
        view_of_a_view = view_by_slice[..., 1:, 10:-10:3]

        _a = pickle.loads(pickle.dumps(a))
        assert _a.sum() == a.sum()
        assert np.array_equal(a, _a)

        _view_by_slice = pickle.loads(pickle.dumps(view_by_slice))
        assert _view_by_slice.sum() == view_by_slice.sum()
        assert np.array_equal(_view_by_slice, view_by_slice)

        _view_of_a_view = pickle.loads(pickle.dumps(view_of_a_view))
        assert _view_of_a_view.sum() == view_of_a_view.sum()
        assert np.array_equal(_view_of_a_view, view_of_a_view)

    def test_viewcasting(self):
        a = SharedNDArray(shape=(1,))
        v = a.view(np.ndarray)
        assert isinstance(v, np.ndarray), type(v)
        assert not isinstance(v, SharedNDArray), type(v)
        a = np.zeros(shape=(1,))
        try:
            v = a.view(SharedNDArray)
        except ValueError:
            pass # we expected this
        else:
            raise AssertionError("We didn't raise the correct exception!")

    def test_auto_unlinking_memory(self):
        import gc
        a = SharedNDArray(shape=(1,))
        name = str(a.shared_memory.name) # Really make sure we don't get a ref
        del a
        gc.collect() # Now memory should be unlinked
        try:
            shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            pass # This is the error we expected if the memory was unlinked.
        else:
            raise AssertionError("We didn't raise the correct exception!")

        # Views should prevent deallocation
        a = SharedNDArray(shape=(10,))
        v = a[:5]
        name = str(a.shared_memory.name) # Really make sure we don't get a ref
        del a
        gc.collect()
        v.sum() # Should still be able to interact with 'v'
        shared_memory.SharedMemory(name=name) # Memory not unlinked yet
        del v
        gc.collect() # Now memory should be unlinked
        try:
            shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            pass # This is the error we expected if the memory was unlinked.
        else:
            raise AssertionError("We didn't raise the correct exception!")

    def test_accessing_unlinked_memory_during_deserialization(self):
        import pickle
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype='uint8')
        string_of_a = pickle.dumps(a)
        del a
        try:
            _a = pickle.loads(string_of_a)
        except FileNotFoundError:
            pass # We expected this error
        else:
            raise AssertionError('Did not get the error we expected')

    def test_accessing_unlinked_memory_in_subprocess(self):
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype='uint8')
        p.store_array(a)
        p.a.sum()
        del a
        try:
            p.a.sum()
        except FileNotFoundError:
            pass # we expected this error
        else:
            import os
            if os.name == 'nt':
                # This is allowed on Windows. Windows will keep memory
                # allocated until all references have been lost from every
                # process.
                pass
            else:
                # However, on posix systems, we expect the system to unlink
                # the memory once the process that originally allocated it
                # loses all references to the array.
                raise AssertionError('Did not get the error we expected')


    def test_serializing_and_deserializing(self):
        """Test serializing/deserializing arrays with random shapes, dtypes, and
        slicing operators.
        """
        for i in range(500):
            self._trial_slicing_of_shared_array()

    def _trial_slicing_of_shared_array(self):
        import pickle
        ri = np.random.randint # Just to get short lines
        dtype = np.dtype(np.random.choice(
            [int, np.uint8, np.uint16, float, np.float32, np.float64]))
        original_dimensions = tuple(
            ri(2, 100) for d in range(ri(2, 5)))
        slicer = tuple(
            slice(
                ri(0, a//2),
                ri(0, a//2)*-1,
                ri(1, min(6, a))
                )
            for a in original_dimensions)
        a = SharedNDArray(shape=original_dimensions, dtype=dtype)
        a.fill(0)
        b = a[slicer] # Should be a view
        b.fill(1)
        expected_total = int(b.sum())
        reloaded_total = int(pickle.loads(pickle.dumps(b)).sum())
        assert expected_total == reloaded_total, \
            f'Failed {dtype.name}/{original_dimensions}/{slicer}'

class TestObjectInSubprocess(MyTestClass):
    class TestClass:
        """Toy class that can be put in a subprocess for testing."""
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            for i, a in enumerate(args):
                setattr(self, f'arg_{i}', a)

        def printing_method(self, *args, **kwargs):
            print(*args, **kwargs)

        def get_attribute(self, attr):
            return getattr(self, attr, None)

        def mirror(self, *args, **kwargs):
            return (args, kwargs)

        def black_hole(self, *args, **kwargs):
            return None

        def get_shape_of_numpy_array(self, ndarray):
            return ndarray.shape

        def fill_and_return_array(self, a, i=1):
            a.fill(i)
            return a

        def sleep(self, seconds):
            import time
            time.sleep(seconds)

        def return_slice(self, a, *args):
            return a[args]

        def sum(self, a):
            return a.sum()

        def store_array(self, a):
            self.a = a

        def nested_method(self, crash=False):
            self._nested_method(crash)

        def _nested_method(self, crash):
            if crash:
                raise ValueError('This error was supposed to be raised')

    def test_create_and_close_object_in_subprocess(self):
        import gc
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        dummy_namespace = p._
        del p
        gc.collect()
        dummy_namespace.child_process.join(timeout=1)
        assert not dummy_namespace.child_process.is_alive()

    def test_passing_normal_numpy_array(self):
        a = np.zeros((3, 3), dtype=int)
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        (_a,), _ = p.mirror(a)
        assert np.array_equal(a, _a), f"{a} != {_a} ({a.dtype}|{_a.dtype}"

    def test_passing_modifying_and_retrieving_shared_array(self):
        a = SharedNDArray(shape=(10, 10), dtype=int)
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        b = p.fill_and_return_array(a, 1)
        assert np.array_equal(a, b)

    def test_attribute_access(self):
        p = ObjectInSubprocess(
            TestObjectInSubprocess.TestClass, 'attribute', x=4)
        assert p.x == 4
        assert getattr(p, 'arg_0') == 'attribute'
        try:
            p.z
        except AttributeError as e: # Get __this__ specific error
            print("Expected attribute error handled by parent process:\n ", e)
        else:
            raise AssertionError('Did not get the error we expected')

    def test_printing_in_child_processes(self):
        a = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        b = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        expected_output = ''
        b.printing_method( 'Hello')
        expected_output += 'Hello\n'
        a.printing_method( 'Hello from subprocess a.')
        expected_output += 'Hello from subprocess a.\n'
        b.printing_method( 'Hello from subprocess b.')
        expected_output += 'Hello from subprocess b.\n'
        a.printing_method( 'Hello world', end=', ', flush=True)
        expected_output += 'Hello world, '
        b.printing_method( 'Hello world!', end='', flush=True)
        expected_output += 'Hello world!'
        return expected_output

    def test_setting_attribute_of_object_in_subprocess(self):
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        assert not hasattr(p, 'z')
        p.z = 10
        assert hasattr(p, 'z')
        assert p.z == 10
        setattr(p, 'z', 100)
        assert p.z == 100
        assert p.get_attribute('z') == 100

    def test_array_values_after_passing_to_subprocess(self):
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        a = SharedNDArray(shape=(10, 1))
        a[:] = 1
        assert a.sum() == p.sum(a)

    def test_object_in_subprocess_overhead(self):
        """Test the overhead of accessing ObjectInSubprocess methods/attributes.
        """
        print('Performance summary:')
        n_loops = 10000
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass, x=4)
        t = self.time_it(
            n_loops, lambda: p.x, timeout_us=100, name='Attribute access')
        print(f" {t:.2f} \u03BCs per get-attribute.")
        t = self.time_it(n_loops, lambda: setattr(p, 'x', 5),
                         timeout_us=100, name='Attribute setting')
        print(f" {t:.2f} \u03BCs per set-attribute.")
        t = self.time_it(n_loops, lambda: p.z, fail=False, timeout_us=200,
                         name='Attribute error')
        print(f" {t:.2f} \u03BCs per parent-handled exception.")
        t = self.time_it(
            n_loops, p.mirror, timeout_us=100, name='Trivial method call')
        print(f" {t:.2f} \u03BCs per trivial method call.")
        self._test_passing_array_performance()

    def _test_passing_array_performance(self):
        """Test the performance of passing random arrays to/from
        ObjectInSubprocess.
        """
        from itertools import product
        pass_by = ['reference', 'serialization']
        methods = ['black_hole', 'mirror']
        shapes = [(10, 10), (1000, 1000)]
        for s, pb, m in product(shapes, pass_by, methods):
            self._test_array_passing(s, pb, m, 'uint8', 1000)

    def _test_array_passing(self, shape, pass_by, method_name, dtype, n_loops):
        dtype = np.dtype(dtype)
        sz = int(np.prod(shape, dtype='uint64')*np.dtype(int).itemsize)
        direction = '<->' if method_name == 'mirror' else '->'
        name = f'{shape} array {direction} {pass_by}'
        shm_obj = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        if pass_by == 'reference':
            a = SharedNDArray(shape, dtype=dtype)
            timeout_us = 5e3
        elif pass_by == 'serialization':
            a = np.zeros(shape=shape, dtype=dtype)
            timeout_us = 1e6
        func = getattr(shm_obj, method_name)
        t_per_loop = self.time_it(n_loops, func, (a,), timeout_us=timeout_us,
                                  name=name)
        print(f' {t_per_loop:.2f} \u03BCs per {name}')

    def test_lock_with_waitlist(self):
        """Test that CustodyThreads stay in order while using resources.
        ObjectsInSubprocess are just mocked as _WaitingList objects.
        """
        import time
        try:
            from tqdm import tqdm
        except ImportError:
            tqdm = None # No progress bars :(

        camera_lock = _WaitingList()
        display_lock = _WaitingList()

        num_snaps = 100
        usage_record = {'camera': [], 'display': []}
        if tqdm is not None:
            pbars = {
                resource: tqdm(
                    total=num_snaps, bar_format='{desc: <30}{n: 3d}-{bar:45}|',
                    desc=f'Threads waiting on {resource}')
                for resource in usage_record.keys()}

        def snap(i, custody):
            if tqdm is not None: pbars['camera'].update(1)
            if tqdm is not None: pbars['camera'].refresh()
            # We're already in line for the camera; wait until we're first
            custody.switch_from(None, camera_lock)
            # Pretend to use the resource
            time.sleep(0.02)
            usage_record['camera'].append(i)

            custody.switch_from(camera_lock, display_lock, wait=False)
            if tqdm is not None: pbars['camera'].update(-1)
            if tqdm is not None: pbars['camera'].refresh()
            if tqdm is not None: pbars['display'].update(1)
            if tqdm is not None: pbars['display'].refresh()
            custody._wait_in_line()
            # Pretend to use the resource
            time.sleep(0.05)
            usage_record['display'].append(i)
            # Move to the next resource
            custody.switch_from(display_lock, None)
            if tqdm is not None: pbars['display'].update(-1)
            if tqdm is not None: pbars['display'].refresh()
            return None

        threads = []
        for i in range(num_snaps):
            threads.append(CustodyThread(
                target=snap, first_resource=camera_lock, args=(i,)).start())
        for th in threads:
            th.get_result()

        if tqdm is not None:
            for pb in pbars.values(): pb.close()

        assert usage_record['camera'] == list(range(num_snaps))
        assert usage_record['display'] == list(range(num_snaps))

    def test_incorrect_thread_management(self):
        """Test accessing an object in a subprocess from multiple threads
        without using a custody object. This is expected to raise a
        RunTimeError.
        """
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        exceptions = []
        def unsafe_fn():
            try:
                p.sleep(.1)
            except RuntimeError: # Should raise this sometimes
                exceptions.append(1)
        threads = [threading.Thread(target=unsafe_fn) for i in range(20)]
        for th in threads: th.start()
        for th in threads: th.join()
        assert len(exceptions) == 19, 'This should have raised some exceptions.'

    def test_sending_shared_arrays(self):
        """Testing sending a SharedNDArray to a ObjectInSubprocess."""

        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype='uint8')

        (_a,), _ = p.mirror(a)
        assert isinstance(_a, SharedNDArray)
        assert _a.shared_memory.name == a.shared_memory.name
        assert _a.offset == a.offset
        assert _a.strides == a.strides

        _a = p.fill_and_return_array(a, 1)
        assert isinstance(_a, SharedNDArray)
        assert _a.shared_memory.name == a.shared_memory.name
        assert _a.offset == a.offset
        assert _a.strides == a.strides

        _a = p.return_slice(a, slice(1, -1), ..., slice(3, 100, 10))
        assert isinstance(_a, SharedNDArray)
        assert _a.shared_memory.name == a.shared_memory.name
        assert _a.offset != a.offset
        assert _a.strides != a.strides

if __name__ == "__main__":
    TestResultThreadAndCustodyThread().run()
    TestSharedNDArray().run()
    TestObjectInSubprocess().run()
