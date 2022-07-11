"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
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
    def __init__(
            self,
            group=None,
            target=None,
            name=None,
            args=(),
            kwargs={},
            *,
            daemon=None):
        super().__init__(group,
                         target,
                         name,
                         args,
                         kwargs,
                         daemon=daemon)
        self.selfLock = threading.Lock()
        # lock itself
        self.selfLock.acquire()

    def run(self):
        self._kwargs['thread'] = self
        if self._target:
            try:
                self._target(*self._args, **self._kwargs)
            except Exception as e:
                print(f'{self.name} thread ended because of exception!: {e}')
                logger.debug(f'{self.name} thread ended because of exception!: {e}')
            finally:
                pass


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
        taskThread = SelfLockThread(None, task, resourceName, args, kwargs, daemon=True)
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
            if callable(target):
                try:
                    target(*args, **kwargs)
                except Exception as e:
                    print(threading.current_thread().name, 'thread exception happened!', e, traceback.format_exc())
                    logger.debug(threading.current_thread().name, 'thread exception happened!', e, traceback.format_exc())

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
        if resourceName not in self.toDeleteList:
            self.toDeleteList[resourceName] = ThreadWaitlist()
        with self.toDeleteList[resourceName] as temp:
            temp.waitlist.append(taskThread)

    def getRunningThread(self, resourceName):
        if resourceName not in self.resources or len(self.resources[resourceName].waitlist) < 1:
            return None
        return self.resources[resourceName].waitlist[0]       

    def clear(self):
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
        if event == 'call':
            return self.localtrace
        else:
            return None
 
    def localtrace(self, frame, event, arg):
        if event == 'exception':
            print('****in local trace: exception stops the thread')
            logger.debug('****in local trace: exception stops the thread')
            raise SystemExit()
        return self.localtrace

    def _raiseError(self, threadId):
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(threadId),
            ctypes.py_object(SystemExit))



class ThreadWaitlist:
    def __init__(self):
        self.waitlistLock = threading.Lock()
        self.waitlist = deque()

    def __enter__(self):
        self.waitlistLock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.waitlistLock.release()
