"""Best-effort stack display telemetry, derived from received camera-frame counts.

This module has no stage or model reference. Coordinates describe the acquisition
plan, not measured hardware positions. Buffer IDs are deliberately not used: they
wrap, and the image display can skip intermediate frames in a camera batch.
"""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Full
from time import monotonic
from typing import Any

from navigate.tools.stack_geometry import StackGeometry, StackReference


@dataclass(frozen=True)
class StackProgressSnapshot:
    """One received plane, with one-based slice, position and timepoint indices."""

    capture_token: tuple[int, str]
    completed: int
    total: int
    plane: int
    planes: int
    channel: str
    position: int
    positions: int
    timepoint: int
    timepoints: int
    z: float
    focus: float
    z_axis: str
    f_axis: str
    start: float
    end: float
    reference_z: float
    relative: bool


@dataclass(frozen=True)
class StackProgressPlan:
    """Small immutable copy of the standard stack's actual acquisition order."""

    capture_token: tuple[int, str]
    geometry: StackGeometry
    references: tuple[StackReference, ...]
    channels: tuple[str, ...]
    defocus: tuple[float, ...]
    cycling: str
    timepoints: int
    z_axis: str
    f_axis: str
    relative: bool

    @property
    def total(self) -> int:
        """Return the frame count across channels, positions and timepoints."""
        return (
            self.geometry.z.count
            * len(self.channels)
            * len(self.references)
            * self.timepoints
        )

    def snapshot(self, completed: int) -> StackProgressSnapshot:
        """Locate the latest received frame in the frozen acquisition plan."""
        if not 1 <= completed <= self.total:
            raise ValueError("Received frame count must be within this acquisition")
        planes, channels = self.geometry.z.count, len(self.channels)
        stack_index, within_stack = divmod(completed - 1, planes * channels)
        timepoint, position = divmod(stack_index, len(self.references))
        if self.cycling == "per_stack":
            channel, plane = divmod(within_stack, planes)
        else:
            plane, channel = divmod(within_stack, channels)
        reference = self.references[position]
        z, focus = self.geometry.position(
            reference,
            plane,
            reference_defocus=self.defocus[0],
            channel_defocus=self.defocus[channel],
        )
        return StackProgressSnapshot(
            self.capture_token,
            completed,
            self.total,
            plane + 1,
            planes,
            self.channels[channel],
            position + 1,
            len(self.references),
            timepoint + 1,
            self.timepoints,
            z,
            focus,
            self.z_axis,
            self.f_axis,
            reference.z + self.geometry.z.start,
            reference.z + self.geometry.z.end,
            reference.z,
            self.relative,
        )


class StackProgressTracker:
    """Publish at most 10 Hz, plus timepoint completion, without blocking acquisition.

    Parameters
    ----------
    plan : StackProgressPlan
        Geometry and ordering captured by the stack feature before receiving data.
    output_queue : queue-like
        Single-slot transport owned by the application. Only nonblocking operations
        are used; intermediate snapshots may be dropped while the GUI is busy.
    """

    def __init__(self, plan: StackProgressPlan, output_queue: Any) -> None:
        self.plan = plan
        self.output_queue = output_queue
        self.completed = 0
        self._last_publish = float("-inf")

    def advance(self, frames: int) -> None:
        """Count a complete camera batch and publish its latest plane when due."""
        if frames <= 0 or self.completed >= self.plan.total:
            return
        self.completed = min(self.completed + frames, self.plan.total)
        now = monotonic()
        frames_per_timepoint = self.plan.total // self.plan.timepoints
        timepoint_complete = self.completed % frames_per_timepoint == 0
        if now - self._last_publish < 0.1 and not timepoint_complete:
            return
        self._last_publish = now
        snapshot = self.plan.snapshot(self.completed)
        try:
            self.output_queue.put_nowait(snapshot)
        except Full:
            try:
                self.output_queue.get_nowait()
            except Empty:
                pass  # A multiprocessing feeder may still own the occupied slot.
            try:
                self.output_queue.put_nowait(snapshot)
            except Full:
                pass
