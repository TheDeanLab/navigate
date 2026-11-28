"""Expose worker exceptions and queue ownership during the remote CI hang."""

import gc
import os
import sys
import threading
import traceback
from typing import Any, Generator

import pytest

DIAGNOSTIC_STREAM = os.fdopen(os.dup(2), "w", buffering=1)


class Probe:
    """Print uncaught worker errors and stop a stalled diagnostic session."""

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_call(self, item: pytest.Item) -> Generator[Any, None, Any]:
        if item.name != "test_lock_with_waitlist":
            return (yield)

        if os.environ.get("NAVIGATE_DIAGNOSTIC_GC") == "1":
            collected = gc.collect()
            print(
                "MAIN THREAD COLLECTION:", collected, file=DIAGNOSTIC_STREAM, flush=True
            )

        previous_hook = threading.excepthook
        previous_unraisable = sys.unraisablehook

        def report(args: threading.ExceptHookArgs) -> None:
            print("\nWORKER EXCEPTION:", file=DIAGNOSTIC_STREAM, flush=True)
            traceback.print_exception(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
                file=DIAGNOSTIC_STREAM,
            )
            DIAGNOSTIC_STREAM.flush()
            previous_hook(args)

        def report_unraisable(args: Any) -> None:
            print(
                "\nUNRAISABLE:",
                args.err_msg,
                repr(args.object),
                file=DIAGNOSTIC_STREAM,
                flush=True,
            )
            traceback.print_exception(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
                file=DIAGNOSTIC_STREAM,
            )
            DIAGNOSTIC_STREAM.flush()
            previous_unraisable(args)

        def snapshot() -> None:
            print("\nQUEUE OWNERSHIP AT HANG:", file=DIAGNOSTIC_STREAM, flush=True)
            frame = sys._current_frames().get(threading.main_thread().ident)
            while (
                frame is not None and frame.f_code.co_name != "test_lock_with_waitlist"
            ):
                frame = frame.f_back
            if frame is not None:
                values = frame.f_locals
                threads = values.get("threads", [])
                indices = {id(thread.custody): i for i, thread in enumerate(threads)}
                for name in ("camera_lock", "display_lock"):
                    resource = values.get(name)
                    print(
                        name,
                        [indices.get(id(custody)) for custody in resource.waiting_list],
                        file=DIAGNOSTIC_STREAM,
                    )
                print(
                    "usage_record", values.get("usage_record"), file=DIAGNOSTIC_STREAM
                )
                for i, thread in enumerate(threads):
                    if not thread.is_alive() or thread.custody.has_custody:
                        print(
                            "THREAD METADATA",
                            i,
                            thread.__dict__,
                            file=DIAGNOSTIC_STREAM,
                        )
                        print(
                            i,
                            "alive",
                            thread.is_alive(),
                            "has_custody",
                            thread.custody.has_custody,
                            "target",
                            (
                                "camera"
                                if thread.custody.target_resource
                                is values.get("camera_lock")
                                else "other"
                            ),
                            "exception",
                            repr(getattr(thread, "exc_value", None)),
                            file=DIAGNOSTIC_STREAM,
                        )
            DIAGNOSTIC_STREAM.flush()
            os._exit(124)

        threading.excepthook = report
        sys.unraisablehook = report_unraisable
        timer = threading.Timer(30, snapshot)
        timer.daemon = True
        timer.start()
        try:
            return (yield)
        finally:
            timer.cancel()
            threading.excepthook = previous_hook
            sys.unraisablehook = previous_unraisable


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    raise SystemExit(pytest.main(sys.argv[1:], plugins=[Probe()]))
