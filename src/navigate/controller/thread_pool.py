# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Standard Library Imports
import os
import threading
import ctypes
import sys
from collections import deque
import logging
import traceback

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SelfLockThread(threading.Thread):
    """A custom thread class with self-locking capabilities.

    This class extends the functionality of the Python threading.Thread class by
    providing the ability to lock and unlock the thread explicitly. It is useful
    in scenarios where thread synchronization and control are required.

    Note
    ----
    - This class provides additional control over thread execution using the
      `wait()` and `unlock()` methods.
    - It allows checking whether the thread is currently locked using the `isLocked()`
      method.
    """

    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=None
    ):
        """Initialize the SelfLockThread.

        Parameters
        ----------
        group : ThreadGroup, optional
            The thread group, by default None
        target : callable, optional
            The target function of the thread, by default None
        name : str, optional
            The name of the thread, by default None
        args : tuple, optional
            The arguments of the target function, by default ()
        kwargs : dict, optional
            The keyword arguments of the target function, by default {}
        daemon : bool, optional
            Whether the thread is daemon, by default None
        """
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        #: threading.Lock: The lock of the thread.
        self.selfLock = threading.Lock()
        # lock itself
        self.selfLock.acquire()

    def run(self):
        """Run the thread."""
        self._kwargs["thread"] = self
        if self._target:
            try:
                self._target(*self._args, **self._kwargs)
            except Exception as e:
                logger.exception(
                    f"{self.name} thread ended because of exception!: {e}",
                    traceback.format_exc(),
                )
            finally:
                pass

    def wait(self):
        """Wait for the thread to finish."""
        self.selfLock.acquire()

    def unlock(self):
        """Unlock the thread."""
        if self.selfLock.locked():
            self.selfLock.release()

    def isLocked(self):
        """Check if the thread is locked.

        Returns
        -------
        bool
            Whether the thread is locked.
        """
        return self.selfLock.locked()


class SynchronizedThreadPool:
    """
    A custom thread pool with synchronization and control features.

    This class provides a thread pool for managing threads associated with different
    resources. It allows registering resources, creating threads, wrapping thread tasks,
    removing threads, and other thread-related operations with explicit control and
    synchronization.

    Note
    ----
    - This class provides explicit control over thread creation, removal,
    and synchronization.
    - It allows managing threads associated with different resources efficiently.
    - The `clear` method moves threads to the `toDeleteList` for later deletion.

    """

    def __init__(self):
        """Initialize the SynchronizedThreadPool."""

        #: dict: The resources of the thread pool.
        self.resources = {}
        #: dict: The toDeleteList of the thread pool.
        self.toDeleteList = {}

    def registerResource(self, resourceName):
        """Register a resource to the pool.

        Parameters
        ----------
        resourceName : str
            The name of the resource.
        """
        if resourceName not in self.resources:
            self.resources[resourceName] = ThreadWaitlist()

    def createThread(
        self,
        resourceName,
        target,
        args=(),
        kwargs={},
        *,
        callback=None,
        cbArgs=(),
        cbKargs={},
    ):
        """Create a thread and add it to the waitlist of the resource.

        Parameters
        ----------
        resourceName : str
            The name of the resource.
        target : callable
            The target function of the thread.
        args : tuple, optional
            The arguments of the target function, by default ()
        kwargs : dict, optional
            The keyword arguments of the target function, by default {}
        callback : callable, optional
            The callback function of the thread, by default None
        cbArgs : tuple, optional
            The arguments of the callback function, by default ()
        cbKargs : dict, optional
            The keyword arguments of the callback function, by default {}

        Returns
        -------
        SelfLockThread
            The created thread.
        """

        if resourceName not in self.resources:
            self.registerResource(resourceName)
        task = self.threadTaskWrapping(
            resourceName, target, callback=callback, cbArgs=cbArgs, cbKargs=cbKargs
        )
        taskThread = SelfLockThread(None, task, resourceName, args, kwargs, daemon=True)
        taskThread.start()
        return taskThread

    def threadTaskWrapping(
        self, resourceName, target, *, callback=None, cbArgs=(), cbKargs={}
    ):
        """Wrap the target function of the thread.

        Parameters
        ----------
        resourceName : str
            The name of the resource.
        target : callable
            The target function of the thread.
        callback : callable, optional
            The callback function of the thread, by default None
        cbArgs : tuple, optional
            The arguments of the callback function, by default ()
        cbKargs : dict, optional
            The keyword arguments of the callback function, by default {}

        Returns
        -------
        callable
            The wrapped target function.
        """

        def func(*args, **kwargs):
            thread = kwargs.get("thread", None)
            if not thread:
                return
            del kwargs["thread"]
            # add thread to the waitlist of the resource
            with self.resources[resourceName] as resource:
                resource.waitlist.append(thread)
                if len(resource.waitlist) == 1:
                    thread.unlock()
            # wait for it's turn
            thread.wait()
            # run itself
            if callable(target):
                try:
                    target(*args, **kwargs)
                except Exception as e:
                    logger.exception(
                        threading.current_thread().name,
                        "thread exception happened!",
                        e,
                        traceback.format_exc(),
                    )

            # wake up next thread if any
            with self.resources[resourceName] as resource:
                resource.waitlist.popleft()
                if len(resource.waitlist) > 0:
                    resource.waitlist[0].unlock()
            # run callback
            if callback:
                callback(*cbArgs, **cbKargs)

        return func

    def removeThread(self, resourceName, taskThread):
        """Remove a thread from the waitlist of the resource.

        Parameters
        ----------
        resourceName : str
            The name of the resource.
        taskThread : SelfLockThread
            The thread to remove.

        Returns
        -------
        bool
            Whether the thread is removed.
        """
        # can only remove waiting threads
        # do not remove running threading
        # if no such resource
        if resourceName not in self.resources:
            return False
        with self.resources[resourceName] as resource:
            # if it is the current running one, kill it and wake up next thread if any
            if resource.waitlist[0] != taskThread:
                # add the thread to toDeleteList
                self.moveToDelete(resourceName, taskThread)
                resource.waitlist.remove(taskThread)
                return

    def moveToDelete(self, resourceName, taskThread):
        """Move a thread to the toDeleteList.

        Parameters
        ----------
        resourceName : str
            The name of the resource.
        taskThread : SelfLockThread
            The thread to move.
        """
        if resourceName not in self.toDeleteList:
            self.toDeleteList[resourceName] = ThreadWaitlist()
        with self.toDeleteList[resourceName] as temp:
            temp.waitlist.append(taskThread)

    def getRunningThread(self, resourceName):
        """Get the running thread of the resource.

        Parameters
        ----------
        resourceName : str
            The name of the resource.

        Returns
        -------
        SelfLockThread
            The running thread.
        """
        if (
            resourceName not in self.resources
            or len(self.resources[resourceName].waitlist) < 1
        ):
            return None
        return self.resources[resourceName].waitlist[0]

    def clear(self):
        """Clear all the threads in the pool."""

        # move all the threads except first one to toDeleteList
        sys.settrace(self.globaltrace)
        for resourceName in self.resources:
            with self.resources[resourceName] as temp:
                headThread = temp.waitlist[0] if len(temp.waitlist) > 0 else None
                for i in range(1, len(temp.waitlist)):
                    self.moveToDelete(resourceName, temp.waitlist[i])
            if headThread:
                self._raiseError(headThread.native_id)
            self.killThreadInList(resourceName, self.toDeleteList)

    def killThreadInList(self, resourceName, threadList):
        """Kill all the threads in the threadList.

        Parameters
        ----------
        resourceName : str
            The name of the resource.
        threadList : dict
            The threadList to kill.
        """
        sys.settrace(self.globaltrace)
        # remove all the threads in threadList
        if resourceName in threadList:
            with threadList[resourceName] as temp:
                while temp.waitlist:
                    thread = temp.waitlist[0]
                    thread.unlock()
                    self._raiseError(thread.native_id)
                    thread.join(1)
                    if not thread.is_alive():
                        # move it from the list
                        temp.waitlist.popleft()
                    else:
                        thread.wait()
                        # move the thread to the end of the list
                        temp.waitlist.popleft()
                        temp.waitlist.append(thread)

    def globaltrace(self, frame, event, arg):
        """Global trace function.

        Parameters
        ----------
        frame : frame
            The frame of the thread.
        event : str
            The event of the thread.
        arg : any
            The argument of the thread.

        Returns
        -------
        callable
            The local trace function if the event is "call", otherwise None.
        """

        if event == "call":
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        """Local trace function.

        Parameters
        ----------
        frame : frame
            The frame of the thread.
        event : str
            The event of the thread.
        arg : any
            The argument of the thread.

        Returns
        -------
        callable
            The local trace function if the event is "exception", otherwise None.
        """

        if event == "exception":
            if os.getenv("GITHUB_ACTIONS") == "true":
                return

            # Silence traceback to avoid printing to console.
            sys.tracebacklimit = 0
            raise SystemExit()
        return self.localtrace

    def _raiseError(self, threadId):
        """Raise error in the thread.

        Parameters
        ----------
        threadId : int
            The id of the thread.
        """

        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_ulong(threadId), ctypes.py_object(SystemExit)
        )


class ThreadWaitlist:
    """A custom thread waitlist with synchronization capabilities."""

    def __init__(self):
        """Initialize the ThreadWaitlist."""
        #: threading.Lock: The lock of the waitlist.
        self.waitlistLock = threading.Lock()
        #: deque: The waitlist.
        self.waitlist = deque()

    def __enter__(self):
        """Enter the context.

        Returns
        -------
        ThreadWaitlist
            The waitlist.
        """
        self.waitlistLock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context.

        Parameters
        ----------
        exc_type : type
            The type of the exception.
        exc_val : any
            The value of the exception.
        exc_tb : traceback
            The traceback of the exception.
        """
        self.waitlistLock.release()
