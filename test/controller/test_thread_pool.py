# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
import time
import unittest
from collections import deque

# Third Party Imports

# Local Imports
from aslm.controller.thread_pool import (
    SelfLockThread,
    SynchronizedThreadPool,
    ThreadWaitlist,
)


class TestSelfLockThread(unittest.TestCase):
    def test_run(self):
        # TODO: Thread not unlocking.

        # Define a target function
        def target_func():
            time.sleep(0.01)
            self.thread.unlock()

        # Create a SelfLockThread instance with the target function
        self.thread = SelfLockThread(target=target_func, name="TestSelfLockThread")

        # Start the thread
        self.thread.run()

        # Wait for the thread to finish
        self.thread.wait()

        # Assert that the thread is not locked anymore
        self.assertFalse(self.thread.isLocked())

    def test_wait(self):
        # TODO: Thread not unlocking.
        # Create a SelfLockThread instance
        thread = SelfLockThread()

        # Start the thread
        thread.start()

        # Assert that the thread is locked
        self.assertTrue(thread.isLocked())

        # Call wait() to release the lock
        thread.wait()

        # Assert that the thread is not locked anymore
        self.assertFalse(thread.isLocked())

    def test_unlock(self):
        # Create a SelfLockThread instance
        thread = SelfLockThread()

        # Start the thread
        thread.start()

        # Assert that the thread is locked
        self.assertTrue(thread.isLocked())

        # Call unlock() to release the lock
        thread.unlock()

        # Assert that the thread is not locked anymore
        self.assertFalse(thread.isLocked())

    def test_isLocked(self):
        # Create a SelfLockThread instance
        thread = SelfLockThread()

        # Assert that the thread is initially locked
        self.assertTrue(thread.isLocked())

        # Call unlock() to release the lock
        thread.unlock()

        # Assert that the thread is not locked anymore
        self.assertFalse(thread.isLocked())


class MockThread:
    def __init__(self, thread_id):
        self.native_id = thread_id
        self.is_alive_result = True
        self.wait_called = False
        self.unlock_called = False

    def is_alive(self):
        return self.is_alive_result

    def wait(self):
        self.wait_called = True

    def unlock(self):
        self.unlock_called = True


class MockThreadWaitlist:
    def __init__(self):
        self.waitlist = deque()


class SynchronizedThreadPoolTest(unittest.TestCase):
    def setUp(self):
        self.thread_pool = SynchronizedThreadPool()

    def test_registerResource(self):
        self.thread_pool.registerResource("resource1")
        self.assertIn("resource1", self.thread_pool.resources)
        # self.assertIsInstance(self.thread_pool.resources["resource1"],
        #                       MockThread)

    def test_createThread(self):
        self.thread_pool.createThread(
            "resource1", target=lambda: print("Hello, World!")
        )
        self.assertIn("resource1", self.thread_pool.resources)
        waitlist = self.thread_pool.resources["resource1"].waitlist
        self.assertEqual(len(waitlist), 1)
        thread = waitlist[0]
        self.assertTrue(thread.is_alive())
        self.assertTrue(thread.wait_called)
        self.assertFalse(thread.unlock_called)

    def test_threadTaskWrapping(self):
        callback_args = ("arg1", "arg2")
        callback_kwargs = {"kwarg1": 123, "kwarg2": "abc"}
        target_called = []
        callback_called = []

        def target_func():
            target_called.append(True)

        def callback_func(arg1, arg2, kwarg1=None, kwarg2=None):
            self.assertEqual(arg1, callback_args[0])
            self.assertEqual(arg2, callback_args[1])
            self.assertEqual(kwarg1, callback_kwargs["kwarg1"])
            self.assertEqual(kwarg2, callback_kwargs["kwarg2"])
            callback_called.append(True)

        wrapped_func = self.thread_pool.threadTaskWrapping(
            "resource1",
            target_func,
            callback=callback_func,
            cbArgs=callback_args,
            cbKargs=callback_kwargs,
        )
        thread = MockThread(1)
        wrapped_func(thread=thread)
        self.assertTrue(target_called[0])
        self.assertTrue(callback_called[0])
        self.assertTrue(thread.wait_called)
        self.assertTrue(thread.unlock_called)

    def test_removeThread(self):
        thread1 = MockThread(1)
        thread2 = MockThread(2)
        self.thread_pool.registerResource("resource1")
        waitlist = self.thread_pool.resources["resource1"].waitlist
        waitlist.extend([thread1, thread2])
        self.thread_pool.removeThread("resource1", thread1)
        self.assertEqual(len(waitlist), 2)
        self.assertEqual(waitlist[0], thread1)
        # self.assertIn("resource1", self.thread_pool.toDeleteList)
        # delete_list = self.thread_pool.toDeleteList["resource1"]
        # self.assertEqual(len(delete_list.waitlist), 1)
        # self.assertEqual(delete_list.waitlist[0], thread1)

    def test_moveToDelete(self):
        thread = MockThread(1)
        self.thread_pool.moveToDelete("resource1", thread)
        self.assertIn("resource1", self.thread_pool.toDeleteList)
        # delete_list = self.thread_pool


class ThreadWaitlistTest(unittest.TestCase):
    def setUp(self):
        self.waitlist = ThreadWaitlist()

    def test_enter(self):
        lock = self.waitlist.waitlistLock
        self.assertFalse(lock.locked())
        with self.waitlist as waitlist:
            self.assertEqual(waitlist, self.waitlist)
            self.assertTrue(lock.locked())

    def test_exit(self):
        lock = self.waitlist.waitlistLock
        lock.acquire()
        self.assertTrue(lock.locked())
        self.waitlist.__exit__(None, None, None)
        self.assertFalse(lock.locked())


if __name__ == "__main__":
    unittest.main()
