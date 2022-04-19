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
        if self._target:
            self._target(*self._args, **self._kwargs)

    def wait(self):
        self.selfLock.acquire()

    def unlock(self):
        if self.selfLock.locked():
            self.selfLock.release()

    def isLocked(self):
        return self.selfLock.locked()


class SynchronizedThreadPool:
    def __init__(self):
        self.resources = {}

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


class ThreadWaitlist:
    def __init__(self):
        self.waitlistLock = threading.Lock()
        self.waitlist = deque()

    def __enter__(self):
        self.waitlistLock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.waitlistLock.release()
