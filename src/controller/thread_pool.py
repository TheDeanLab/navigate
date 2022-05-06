"""
ASLM thread pool.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

import threading
import time
import ctypes
from collections import deque


class SelfLockThread(threading.Thread):
    def __init__(
            self,
            group=None,
            target=None,
            name=None,
            args=(),
            kwargs={},
            *,
            daemon=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.selfLock = threading.Lock()
        # lock itself
        self.selfLock.acquire()

    def run(self):
        self._kwargs['thread'] = self
        self._thread_id = threading.get_native_id()
        if self._target:
            try:
                self._target(*self._args, **self._kwargs)
            finally:
                print('thread ended!!!')

    def wait(self):
        self.selfLock.acquire()

    def unlock(self):
        if self.selfLock.locked():
            self.selfLock.release()

    def isLocked(self):
        return self.selfLock.locked()

    def _getId(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
    
    def stop(self):
        # add an SystemExit Exception to the thread
        # reference: https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread
        thread_id = self._getId()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        return res <= 1


class SynchronizedThreadPool:
    def __init__(self):
        self.resources = {}
        self.toDeleteList = {}

    def registerResource(self, resourceName):
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
            cbKargs={}):
        if resourceName not in self.resources:
            self.registerResource(resourceName)
        task = self.threadTaskWrapping(
            resourceName,
            target,
            callback=callback,
            cbArgs=cbArgs,
            cbKargs=cbKargs)
        taskThread = SelfLockThread(None, task, None, args, kwargs)
        taskThread.start()
        return taskThread

    def threadTaskWrapping(
            self,
            resourceName,
            target,
            *,
            callback=None,
            cbArgs=(),
            cbKargs={}):
        def func(*args, **kwargs):
            thread = kwargs.get('thread', None)
            if not thread:
                return
            del kwargs['thread']
            # add thread to the waitlist of the resource
            with self.resources[resourceName] as resource:
                resource.waitlist.append(thread)
                if len(resource.waitlist) == 1:
                    thread.unlock()
            # wait for it's turn
            thread.wait()
            # run itself
            if target:
                target(*args, **kwargs)
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
        # if no such resource
        if resourceName not in self.resources:
            return False
        with self.resources[resourceName] as resource:
            # if it is the current running one, kill it and wake up next thread if any
            if resource.waitlist[0] == taskThread:
                while taskThread.is_alive():
                    taskThread.stop()
                    time.sleep(0.1)
                resource.waitlist.popleft()
                self.killThreadInList(resourceName, self.toDeleteList)
                if len(resource.waitlist) > 0:
                    resource.waitlist[0].unlock()
            else:
                # add the thread to toDeleteList
                if resourceName not in self.toDeleteList:
                    self.toDeleteList[resourceName] = ThreadWaitlist()
                with self.toDeleteList[resourceName] as temp:
                    temp.waitlist.append(taskThread)
                resource.waitlist.remove(taskThread)

    def clear(self):
        # remove all the threads
        for resourceName in self.resources:
            self.killThreadInList(resourceName, self.resources)
            self.killThreadInList(resourceName, self.toDeleteList)

    def killThreadInList(self, resourceName, threadList):
        # remove all the threads in threadList
        if resourceName in threadList:
            with threadList[resourceName] as temp:
                while temp.waitlist:
                    thread = temp.waitlist[0]
                    thread.unlock()
                    while thread.is_alive():
                        thread.stop()
                        time.sleep(0.1)
                    temp.waitlist.popleft()



class ThreadWaitlist:
    def __init__(self):
        self.waitlistLock = threading.Lock()
        self.waitlist = deque()

    def __enter__(self):
        self.waitlistLock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.waitlistLock.release()
