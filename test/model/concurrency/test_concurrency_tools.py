from aslm.model.concurrency.concurrency_tools import (
    ResultThread,
    CustodyThread,
    SharedNDArray,
    ObjectInSubprocess,
    _WaitingList,
)

from multiprocessing import shared_memory

import numpy as np
import threading

# Printing from a child process is tricky:
import io
from contextlib import redirect_stdout

# Handling exceptions from a child process/thread is tricky:
import traceback


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

    def run(self, test_prefix="test_", fail=False, fail_fast=False):
        """Runs all methods that begin with `test_prefix`"""
        tests = [i for i in dir(self) if i.startswith(test_prefix)]
        tests = [i for i in tests if callable(getattr(self, i))]

        print("#" * 80)
        print(f'{f" Running Tests of {self.__class__.__name__} ":#^80s}')
        print("#" * 80)
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
        name = t[5:].replace("_", " ")
        print(f'{f"     {i+1} of {self.num_tests} | Testing {name}    ":-^80s}')
        try:
            with redirect_stdout(printed_output):
                expected_output = getattr(self, t)()
            if expected_output is not None:
                o = printed_output.getvalue()
                assert expected_output == o, (
                    f"\n Returned result:\n"
                    f"    `{repr(o)}`\n"
                    f" Did not match expected output:\n"
                    f'     "{repr(expected_output)}"\n'
                )
        except Exception:
            print("v" * 80)
            print(traceback.format_exc().strip("\n"))
            print("^" * 80)
            print("v" * 80)
            print(printed_output.getvalue())
            print("^" * 80)
            return False
        else:
            self.num_passed += 1
            if printed_output.getvalue():
                for ll in printed_output.getvalue().strip("\n").split("\n"):
                    print(f"   {ll}")
            print(f'{f"> Success <":-^80s}')
            return True

    def _summarize_results(self):
        fill = "#" if self.num_passed == self.num_tests else "!"
        print(fill * 80)
        message = (
            f"Completed Tests for {self.__class__.__name__} "
            f"-- passed {self.num_passed} of {self.num_tests}"
        )
        if self.num_passed == self.num_tests:
            print(f'{f"  {message}  ":#^80s}')
        else:
            print(f'{f"  {message}  ":!^80s}')
        print(fill * 80)
        print()
        return self.num_passed == self.num_tests

    def time_it(
        self,
        n_loops,
        func,
        args=None,
        kwargs=None,
        fail=True,
        timeout_us=None,
        name=None,
    ):
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
            tqdm = None  # No progress bars :(
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        if tqdm is not None:
            f = "{desc: <38}{n: 7d}-{bar:17}|[{rate_fmt}]"
            pb = tqdm(total=n_loops, desc=name, bar_format=f)
        start = time.perf_counter()
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
        end = time.perf_counter()
        if tqdm is not None:
            pb.close()
        time_per_loop_us = ((end - start) / n_loops) * 1e6
        if timeout_us is not None:
            if time_per_loop_us > timeout_us:
                name = func.__name__ if name is None else name
                raise TimeoutError(
                    f"Timed out on {name}\n"
                    f"   args:{args}\n"
                    f"   kwargs: {kwargs}\n"
                    f" Each loop took {time_per_loop_us:.2f} \u03BCs"
                    f" (Allowed: {timeout_us:.2f} \u03BCs)"
                )
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
        assert hasattr(th, "_return")
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
        # Create a mock function e() that raises an exception

        def e():
            raise ValueError("Don't worry, this exception occurred on purpose!")

        th = ResultThread(target=e).start()
        th.join()  # join won't reraise exception in main thread
        assert hasattr(th, "exc_value")
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

        CustodyThread(target=custody_f, first_resource=None).start()
        # CustodyThread accepts a target with a positional arg 'custody'

        def custody_f(custody):
            return 1

        CustodyThread(target=custody_f, first_resource=None).start()

        # CustodyThread will otherwise raise a ValueError
        def f():
            return 1

        try:
            CustodyThread(target=f, first_resource=None).start()
        except ValueError:
            pass  # We expect this
        else:
            raise AssertionError("We didn't get the exception we expected...")

        def f(a):
            return 1

        try:
            CustodyThread(target=f, first_resource=None).start()
        except ValueError:
            pass  # We expect this
        else:
            raise AssertionError("We didn't get the exception we expected...")

        def f(a=1):
            return 1

        try:
            CustodyThread(target=f, first_resource=None).start()
        except ValueError:
            pass  # We expect this
        else:
            raise AssertionError("We didn't get the exception we expected...")

    def test_providing_first_resource(self):
        resource = _WaitingList()
        mutable_variables = {"step": 0, "progress": 0}

        def f(custody):
            while mutable_variables["step"] == 0:
                pass
            custody.switch_from(None, resource)
            mutable_variables["progress"] += 1
            while mutable_variables["step"] == 1:
                pass
            custody.switch_from(resource, None)
            mutable_variables["progress"] += 1
            return

        try:
            th = CustodyThread(target=f, first_resource=resource).start()
            assert hasattr(th, "custody"), "Should have a custody attribute."
            assert not th.custody.has_custody, "Should not have custody yet."
            assert th.custody.target_resource is resource, "Should be in line."
            # Make target thread progress one step and acquire custody
            mutable_variables["step"] = 1
            while mutable_variables["progress"] == 0:
                pass  # Wait for thread
            assert th.custody.has_custody, "Should have gotten custody."
            assert th.custody.target_resource is resource
            # Make target thread progress one step, release custody, and exit
            mutable_variables["step"] = 2
            while mutable_variables["progress"] == 1:
                pass  # Wait for thread
            assert not th.custody.has_custody
            assert th.custody.target_resource is None
            th.join()
        finally:  # if anything goes wrong, make sure the thread exits
            mutable_variables["step"] = -1


class TestSharedNDArray(MyTestClass):
    """Various tests of the SharedNDArray class"""

    def test_subclassed_numpy_array_types(self):
        a = SharedNDArray(shape=(1,), dtype="uint8")
        assert isinstance(a, SharedNDArray)
        assert isinstance(a, np.ndarray)
        assert type(a) is SharedNDArray, type(a)
        assert type(a) is not np.ndarray
        assert hasattr(a, "shared_memory")
        assert isinstance(a.shared_memory, shared_memory.SharedMemory)

    def test_ndarraylike_behavior(self):
        """Testing if we broke how an ndarray is supposed to behave."""
        ri = np.random.randint  # Just to get short lines
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype="uint8")
        c = ri(0, 255, original_dimensions, dtype="uint8")
        a[:] = c  # Fill 'a' with 'c's random values
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

        ri = np.random.randint  # Just to get short lines
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype="uint8")
        c = ri(0, 255, original_dimensions, dtype="uint8")
        a[:] = c  # Fill 'a' with 'c's random values
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
            pass  # we expected this
        else:
            raise AssertionError("We didn't raise the correct exception!")

    def test_auto_unlinking_memory(self):
        import gc

        a = SharedNDArray(shape=(1,))
        name = str(a.shared_memory.name)  # Really make sure we don't get a ref
        del a
        gc.collect()  # Now memory should be unlinked
        try:
            shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            pass  # This is the error we expected if the memory was unlinked.
        else:
            raise AssertionError("We didn't raise the correct exception!")

        # Views should prevent deallocation
        a = SharedNDArray(shape=(10,))
        v = a[:5]
        name = str(a.shared_memory.name)  # Really make sure we don't get a ref
        del a
        gc.collect()
        v.sum()  # Should still be able to interact with 'v'
        shared_memory.SharedMemory(name=name)  # Memory not unlinked yet
        del v
        gc.collect()  # Now memory should be unlinked
        try:
            shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            pass  # This is the error we expected if the memory was unlinked.
        else:
            raise AssertionError("We didn't raise the correct exception!")

    def test_accessing_unlinked_memory_during_deserialization(self):
        import pickle

        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype="uint8")
        string_of_a = pickle.dumps(a)
        del a
        try:
            _a = pickle.loads(string_of_a)
        except FileNotFoundError:
            pass  # We expected this error
        else:
            raise AssertionError("Did not get the error we expected")

    def test_accessing_unlinked_memory_in_subprocess(self):
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype="uint8")
        p.store_array(a)
        p.a.sum()
        del a
        try:
            p.a.sum()
        except FileNotFoundError:
            pass  # we expected this error
        else:
            import os

            if os.name == "nt":
                # This is allowed on Windows. Windows will keep memory
                # allocated until all references have been lost from every
                # process.
                pass
            else:
                # However, on posix systems, we expect the system to unlink
                # the memory once the process that originally allocated it
                # loses all references to the array.
                raise AssertionError("Did not get the error we expected")

    def test_serializing_and_deserializing(self):
        """Test serializing/deserializing arrays with random shapes, dtypes, and
        slicing operators.
        """
        for i in range(500):
            self._trial_slicing_of_shared_array()

    def _trial_slicing_of_shared_array(self):
        import pickle

        ri = np.random.randint  # Just to get short lines
        dtype = np.dtype(
            np.random.choice([int, np.uint8, np.uint16, float, np.float32, np.float64])
        )
        original_dimensions = tuple(ri(2, 100) for d in range(ri(2, 5)))
        slicer = tuple(
            slice(ri(0, a // 2), ri(0, a // 2) * -1, ri(1, min(6, a)))
            for a in original_dimensions
        )
        a = SharedNDArray(shape=original_dimensions, dtype=dtype)
        a.fill(0)
        b = a[slicer]  # Should be a view
        b.fill(1)
        expected_total = int(b.sum())
        reloaded_total = int(pickle.loads(pickle.dumps(b)).sum())
        assert (
            expected_total == reloaded_total
        ), f"Failed {dtype.name}/{original_dimensions}/{slicer}"


class TestObjectInSubprocess(MyTestClass):
    class TestClass:
        """Toy class that can be put in a subprocess for testing."""

        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            for i, a in enumerate(args):
                setattr(self, f"arg_{i}", a)

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
                raise ValueError("This error was supposed to be raised")

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
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass, "attribute", x=4)
        assert p.x == 4
        assert getattr(p, "arg_0") == "attribute"
        try:
            p.z
        except AttributeError as e:  # Get __this__ specific error
            print("Expected attribute error handled by parent process:\n ", e)
        else:
            raise AssertionError("Did not get the error we expected")

    def test_printing_in_child_processes(self):
        a = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        b = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        expected_output = ""
        b.printing_method("Hello")
        expected_output += "Hello\n"
        a.printing_method("Hello from subprocess a.")
        expected_output += "Hello from subprocess a.\n"
        b.printing_method("Hello from subprocess b.")
        expected_output += "Hello from subprocess b.\n"
        a.printing_method("Hello world", end=", ", flush=True)
        expected_output += "Hello world, "
        b.printing_method("Hello world!", end="", flush=True)
        expected_output += "Hello world!"
        return expected_output

    def test_setting_attribute_of_object_in_subprocess(self):
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        assert not hasattr(p, "z")
        p.z = 10
        assert hasattr(p, "z")
        assert p.z == 10
        setattr(p, "z", 100)
        assert p.z == 100
        assert p.get_attribute("z") == 100

    def test_array_values_after_passing_to_subprocess(self):
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        a = SharedNDArray(shape=(10, 1))
        a[:] = 1
        assert a.sum() == p.sum(a)

    def test_object_in_subprocess_overhead(self):
        """Test the overhead of accessing ObjectInSubprocess methods/attributes."""
        print("Performance summary:")
        n_loops = 10000
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass, x=4)
        t = self.time_it(n_loops, lambda: p.x, timeout_us=100, name="Attribute access")
        print(f" {t:.2f} \u03BCs per get-attribute.")
        t = self.time_it(
            n_loops,
            lambda: setattr(p, "x", 5),
            timeout_us=100,
            name="Attribute setting",
        )
        print(f" {t:.2f} \u03BCs per set-attribute.")
        t = self.time_it(
            n_loops, lambda: p.z, fail=False, timeout_us=200, name="Attribute error"
        )
        print(f" {t:.2f} \u03BCs per parent-handled exception.")
        t = self.time_it(n_loops, p.mirror, timeout_us=100, name="Trivial method call")
        print(f" {t:.2f} \u03BCs per trivial method call.")
        self._test_passing_array_performance()

    def _test_passing_array_performance(self):
        """Test the performance of passing random arrays to/from
        ObjectInSubprocess.
        """
        from itertools import product

        pass_by = ["reference", "serialization"]
        methods = ["black_hole", "mirror"]
        shapes = [(10, 10), (1000, 1000)]
        for s, pb, m in product(shapes, pass_by, methods):
            self._test_array_passing(s, pb, m, "uint8", 1000)

    def _test_array_passing(self, shape, pass_by, method_name, dtype, n_loops):
        dtype = np.dtype(dtype)
        int(np.prod(shape, dtype="uint64") * np.dtype(int).itemsize)
        direction = "<->" if method_name == "mirror" else "->"
        name = f"{shape} array {direction} {pass_by}"
        shm_obj = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        if pass_by == "reference":
            a = SharedNDArray(shape, dtype=dtype)
            timeout_us = 5e3
        elif pass_by == "serialization":
            a = np.zeros(shape=shape, dtype=dtype)
            timeout_us = 1e6
        func = getattr(shm_obj, method_name)
        t_per_loop = self.time_it(n_loops, func, (a,), timeout_us=timeout_us, name=name)
        print(f" {t_per_loop:.2f} \u03BCs per {name}")

    def test_lock_with_waitlist(self):
        """Test that CustodyThreads stay in order while using resources.
        ObjectsInSubprocess are just mocked as _WaitingList objects.
        """
        import time

        try:
            from tqdm import tqdm
        except ImportError:
            tqdm = None  # No progress bars :(

        camera_lock = _WaitingList()
        display_lock = _WaitingList()

        num_snaps = 100
        usage_record = {"camera": [], "display": []}
        if tqdm is not None:
            pbars = {
                resource: tqdm(
                    total=num_snaps,
                    bar_format="{desc: <30}{n: 3d}-{bar:45}|",
                    desc=f"Threads waiting on {resource}",
                )
                for resource in usage_record.keys()
            }

        def snap(i, custody):
            if tqdm is not None:
                pbars["camera"].update(1)
            if tqdm is not None:
                pbars["camera"].refresh()
            # We're already in line for the camera; wait until we're first
            custody.switch_from(None, camera_lock)
            # Pretend to use the resource
            time.sleep(0.02)
            usage_record["camera"].append(i)

            custody.switch_from(camera_lock, display_lock, wait=False)
            if tqdm is not None:
                pbars["camera"].update(-1)
            if tqdm is not None:
                pbars["camera"].refresh()
            if tqdm is not None:
                pbars["display"].update(1)
            if tqdm is not None:
                pbars["display"].refresh()
            custody._wait_in_line()
            # Pretend to use the resource
            time.sleep(0.05)
            usage_record["display"].append(i)
            # Move to the next resource
            custody.switch_from(display_lock, None)
            if tqdm is not None:
                pbars["display"].update(-1)
            if tqdm is not None:
                pbars["display"].refresh()
            return None

        threads = []
        for i in range(num_snaps):
            threads.append(
                CustodyThread(
                    target=snap, first_resource=camera_lock, args=(i,)
                ).start()
            )
        for th in threads:
            th.get_result()

        if tqdm is not None:
            for pb in pbars.values():
                pb.close()

        assert usage_record["camera"] == list(range(num_snaps))
        assert usage_record["display"] == list(range(num_snaps))

    def test_incorrect_thread_management(self):
        """Test accessing an object in a subprocess from multiple threads
        without using a custody object. This is expected to raise a
        RunTimeError.
        """
        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        exceptions = []

        def unsafe_fn():
            try:
                p.sleep(0.1)
            except RuntimeError:  # Should raise this sometimes
                exceptions.append(1)

        threads = [threading.Thread(target=unsafe_fn) for i in range(20)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        assert len(exceptions) == 19, "This should have raised some exceptions."

    def test_sending_shared_arrays(self):
        """Testing sending a SharedNDArray to a ObjectInSubprocess."""

        p = ObjectInSubprocess(TestObjectInSubprocess.TestClass)
        original_dimensions = (3, 3, 3, 256, 256)
        a = SharedNDArray(shape=original_dimensions, dtype="uint8")

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
