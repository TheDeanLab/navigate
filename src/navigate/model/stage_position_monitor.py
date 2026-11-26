"""Best-effort idle stage telemetry with operation and shutdown coordination."""

from __future__ import annotations

import logging
import math
import queue
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, TypedDict

from navigate.config.stage_settings import stage_position_polling_supported
from navigate.model.devices.stage.readback import StagePositionReadback

if TYPE_CHECKING:
    from navigate.model.model import Model


class StagePositionSnapshot(TypedDict):
    """Confirmed axis positions with identity and monotonic sampling time."""

    microscope_name: str
    sample_started: float
    positions: dict[str, float]
    unavailable_axes: list[str]


def suspend_stage_polling(method: Callable[..., Any]) -> Callable[..., Any]:
    """Suspend telemetry for a model operation, including nested operations."""

    @wraps(method)
    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        monitor = getattr(self, "_stage_position_monitor", None)
        if monitor is None:
            return method(self, *args, **kwargs)
        with monitor.suspended():
            return method(self, *args, **kwargs)

    return wrapped


class StagePositionMonitor:
    """One worker for idle readbacks; never queue missed polling intervals.

    Reads are enabled by default for capable devices. Set ``position_polling``
    to false in a microscope's stage configuration to opt out. Live acquisition
    is deliberately excluded. Polling never updates acquisition position caches.

    Parameters
    ----------
    model : Model
        Model owning the hardware and acquisition lifecycle.
    output_queue : multiprocessing.Queue
        Dedicated single-slot transport; publishing never blocks hardware work.
    clock : Callable
        Monotonic clock, injectable for deterministic scheduling tests.
    """

    def __init__(
        self,
        model: Model,
        output_queue: Any,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.model = model
        self.output_queue = output_queue
        self.clock = clock
        self._condition = threading.Condition()
        self._suspensions = 0
        self._reading = False
        self._generation = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._retry: dict[int, tuple[float, int]] = {}
        self._logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Start once, after model and controller initialization have completed."""
        if self._thread is None and not self._stop.is_set():
            self._thread = threading.Thread(
                target=self._run, name="Idle stage positions", daemon=True
            )
            self._thread.start()

    def close(self) -> None:
        """Wake the worker and finish its bounded read before devices close."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join()

    @contextmanager
    def suspended(self) -> Iterator[None]:
        """Prevent new reads and drain the current transaction before an operation.

        The condition is released during I/O and during the operation. Nested
        operations and Stop Stages therefore do not wait on one another.
        """
        with self._condition:
            self._suspensions += 1
            self._generation += 1
            while self._reading:
                self._condition.wait()
        try:
            yield
        finally:
            with self._condition:
                self._suspensions -= 1

    def _idle(self) -> bool:
        model = self.model
        return not (
            self._stop.is_set()
            or self._suspensions
            or model.is_acquiring
            or getattr(model, "_prepared_camera_token", None) is not None
            or getattr(model, "_resolution_change_task", None) is not None
            or any(
                thread is not None and thread.is_alive()
                for thread in (model.signal_thread, model.data_thread)
            )
            or any(scope.camera.is_acquiring for scope in model.microscopes.values())
        )

    def _publish(self, snapshot: StagePositionSnapshot) -> None:
        try:
            self.output_queue.put_nowait(snapshot)
        except queue.Full:
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                pass  # A multiprocessing queue's feeder may still own the slot.
            try:
                self.output_queue.put_nowait(snapshot)
            except queue.Full:
                pass

    def poll_once(self) -> None:
        """Attempt one idle cycle, checking eligibility before each device read."""
        with self._condition:
            if not self._idle():
                return
            microscope = self.model.active_microscope
            name = self.model.active_microscope_name
            generation = self._generation
        configuration = self.model.configuration
        if microscope is None or name is None or configuration is None:
            return
        enabled = configuration["configuration"]["microscopes"][name]["stage"].get(
            "position_polling", True
        )
        if not enabled:
            return
        snapshot: StagePositionSnapshot = {
            "microscope_name": name,
            "sample_started": self.clock(),
            "positions": {},
            "unavailable_axes": [],
        }
        groups: dict[int, tuple[list[StagePositionReadback], set[str]]] = {}
        stage_config = configuration["configuration"]["microscopes"][name]["stage"]
        hardware = stage_config.get("hardware", [])
        if hasattr(hardware, "get"):
            hardware = [hardware]
        supported_axes = {
            axis
            for device in hardware
            if stage_position_polling_supported(
                {"hardware": device}, getattr(microscope, "is_synthetic", False)
            )
            for axis in device.get("axes", [])
        }
        for stage, axes in microscope.stages_list:
            # Use the same configured-device eligibility as the GUI toggle.
            # Inheriting a readback implementation does not opt a plugin in.
            if not isinstance(stage, StagePositionReadback) or not set(axes).issubset(
                supported_axes
            ):
                snapshot["unavailable_axes"].extend(axes)
                continue
            identity = id(stage.position_readback_identity)
            stages, group_axes = groups.setdefault(identity, ([], set()))
            if stage not in stages:
                stages.append(stage)
            group_axes.update(axes)
        for identity, (stages, axes) in groups.items():
            due, failures = self._retry.get(identity, (0.0, 0))
            if self.clock() < due:
                snapshot["unavailable_axes"].extend(axes)
                continue
            with self._condition:
                if (
                    not self._idle()
                    or generation != self._generation
                    or not configuration["configuration"]["microscopes"][name][
                        "stage"
                    ].get("position_polling", True)
                ):
                    return
                self._reading = True
            started = self.clock()
            try:
                positions = stages[0].read_position_for_monitor(tuple(stages[1:]))
                if positions is not None:
                    expected = {f"{axis}_pos" for axis in axes}
                    if not expected.issubset(positions) or not all(
                        math.isfinite(positions[key]) for key in expected
                    ):
                        raise ValueError("Incomplete or nonfinite stage readback")
                    snapshot["positions"].update(
                        {key: round(positions[key], 2) for key in expected}
                    )
                    # At most one query/second and approximately 5% readback duty.
                    self._retry[identity] = (
                        started + max(1.0, 20 * (self.clock() - started)),
                        0,
                    )
                else:
                    snapshot["unavailable_axes"].extend(axes)
            except Exception:
                failures += 1
                self._retry[identity] = (
                    self.clock() + min(30.0, 2 ** min(failures, 5)),
                    failures,
                )
                snapshot["unavailable_axes"].extend(axes)
                if failures == 1:
                    self._logger.warning(
                        "Idle stage readback failed for %s; backing off",
                        name,
                        exc_info=True,
                    )
            finally:
                with self._condition:
                    self._reading = False
                    self._condition.notify_all()
        with self._condition:
            if (
                self._idle()
                and generation == self._generation
                and microscope is self.model.active_microscope
                and configuration["configuration"]["microscopes"][name]["stage"].get(
                    "position_polling", True
                )
            ):
                self._publish(snapshot)

    def _run(self) -> None:
        failures = 0
        delay = 1.0
        while not self._stop.wait(delay):
            try:
                self.poll_once()
            except Exception:
                failures = min(failures + 1, 5)
                delay = min(30.0, 2**failures)
                self._logger.exception(
                    "Idle stage monitor failed; retrying in %.1f seconds", delay
                )
            else:
                failures = 0
                delay = 1.0
