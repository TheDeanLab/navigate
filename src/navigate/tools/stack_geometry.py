# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

"""Pure stack geometry shared by GUI previews and acquisition features.

Z and focus denote the selected stacking roles, not fixed hardware axes. Origins
are supplied by the caller after microscope offsets, position-table selection,
or autofocus. This module performs no I/O and never changes configuration.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import ceil
from typing import Any


def stack_position(start: float, origin: float, step: float, index: int) -> float:
    """Resolve an indexed offset using the existing acquisition arithmetic.

    Parameters
    ----------
    start : float
        Starting offset from the reference position.
    origin : float
        Reference position in the selected device's coordinates.
    step : float
        Signed increment between planes.
    index : int
        Plane index. May equal the plane count while advancing a feature before
        its end-of-stack check; this does not request an additional exposure.
    """
    return start + origin + index * step


def focus_position(
    start: float,
    origin: float,
    step: float,
    index: int,
    reference_defocus: float = 0.0,
    channel_defocus: float = 0.0,
) -> float:
    """Resolve focus, retaining the first selected channel as its reference.

    Parameters
    ----------
    start, origin, step : float
        Starting focus offset, reference position, and signed focus increment.
    index : int
        Plane index.
    reference_defocus : float, optional
        Defocus of the first selected channel, already included in ``start``.
    channel_defocus : float, optional
        Defocus of the channel being acquired.
    """
    return (
        stack_position(start - reference_defocus, origin, step, index) + channel_defocus
    )


@dataclass(frozen=True)
class StackAxis:
    """Requested boundaries and sampling for one stacking role.

    The end boundary is not generally the last acquired plane. Explicit plane
    counts and step signs are authoritative, including those supplied by custom
    workflows; they are not inferred again from the boundaries.
    """

    start: float
    end: float
    step: float
    count: int

    @classmethod
    def from_bounds(
        cls, start: float, end: float, step: float, *, flipped: bool = False
    ) -> StackAxis:
        """Apply the GUI's ceiling count and configured stage direction.

        Parameters
        ----------
        start, end : float
            Requested offsets, retained in their supplied order.
        step : float
            Positive step magnitude.
        flipped : bool, optional
            Whether the configured stage direction negates the step.
        """
        if step <= 0:
            raise ValueError("Stack step magnitude must be positive")
        count = ceil(abs((end - start) / step))
        return cls(start, end, step * (-1 if flipped else 1), count)

    @classmethod
    def from_legacy_z(cls, state: Mapping[str, Any]) -> StackAxis:
        """Read only the four existing Z fields, preserving the configured count."""
        return cls(
            float(state["start_position"]),
            float(state["end_position"]),
            float(state["step_size"]),
            int(state["number_z_steps"]),
        )

    @classmethod
    def focus_ramp(cls, start: float, end: float, count: int) -> StackAxis:
        """Interpolate focus over ``count`` intervals, as in existing acquisitions.

        Parameters
        ----------
        start, end : float
            Requested focus offsets at the stack boundaries.
        count : int
            Number of acquired planes. Zero retains the legacy division error;
            an empty GUI preview must not construct an acquisition focus ramp.
        """
        return cls(start, end, (end - start) / count, count)

    @property
    def distance(self) -> float:
        """Return the requested extent used for stage-movement timing."""
        return abs(self.start - self.end)

    def position(self, origin: float, index: int) -> float:
        """Return an indexed coordinate relative to the supplied origin."""
        return stack_position(self.start, origin, self.step, index)


@dataclass(frozen=True)
class StackReference:
    """Coordinates anchoring a stack, selected by the acquisition workflow."""

    z: float
    focus: float

    @classmethod
    def for_single_position(
        cls,
        state: Mapping[str, Any],
        current_z: float,
        current_focus: float,
        *,
        use_current: bool = False,
    ) -> StackReference:
        """Preserve saved-origin versus current/autofocus-origin selection.

        Parameters
        ----------
        state : Mapping
            Existing microscope state; missing saved origins use current values.
        current_z, current_focus : float
            Positions of the selected axes, supplied by the caller.
        use_current : bool, optional
            Existing acquisition ``get_origin`` behavior. Position-table rows
            already contain their references and do not use this selector.
        """
        if use_current:
            return cls(current_z, current_focus)
        return cls(
            state.get("stack_z_origin", current_z),
            state.get("stack_focus_origin", current_focus),
        )


@dataclass(frozen=True)
class StackGeometry:
    """A stack's offset geometry, independent of its position or microscope."""

    z: StackAxis
    focus: StackAxis

    def __post_init__(self) -> None:
        if self.z.count != self.focus.count:
            raise ValueError("Z and focus must have the same plane count")

    @classmethod
    def from_legacy_state(cls, state: Mapping[str, Any]) -> StackGeometry:
        """Snapshot the existing acquisition fields without recomputing their count."""
        z = StackAxis.from_legacy_z(state)
        return cls(
            z,
            StackAxis.focus_ramp(
                float(state["start_focus"]), float(state["end_focus"]), z.count
            ),
        )

    def position(
        self,
        reference: StackReference,
        index: int,
        *,
        reference_defocus: float = 0.0,
        channel_defocus: float = 0.0,
    ) -> tuple[float, float]:
        """Return the Z/focus target for a plane and channel at one reference."""
        return (
            self.z.position(reference.z, index),
            focus_position(
                self.focus.start,
                reference.focus,
                self.focus.step,
                index,
                reference_defocus,
                channel_defocus,
            ),
        )

    def first_plane(self, reference: StackReference) -> tuple[float, float] | None:
        """Return the first sampled plane, or None for an empty preview."""
        return self.position(reference, 0) if self.z.count > 0 else None

    def last_plane(self, reference: StackReference) -> tuple[float, float] | None:
        """Return the last sampled plane, distinct from the requested end boundary."""
        return self.position(reference, self.z.count - 1) if self.z.count > 0 else None
