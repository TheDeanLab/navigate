"""Resolve relative stacks once, before preparing acquisition hardware."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import TYPE_CHECKING, Any

from navigate.tools.stack_geometry import StackGeometry, StackReference

if TYPE_CHECKING:
    from navigate.model.model import Model


@dataclass(frozen=True)
class RelativeStackPlan:
    """Acquisition geometry and references, frozen across channels and timepoints."""

    microscope_name: str
    z_axis: str
    f_axis: str
    geometry: StackGeometry
    reference: StackReference
    headers: tuple[str, ...] = ()
    positions: tuple[tuple[float, ...], ...] = ()

    def legacy_fields(self) -> dict[str, float | int]:
        """Return the existing fields consumed by features, waveforms and saving."""
        return self.geometry.legacy_fields(self.reference)


def relative_geometry(state: Any, stage_config: Any) -> StackGeometry:
    """Resolve relative settings without changing the experiment or touching hardware."""
    ramp = state.get("relative_focus_ramp", False)
    return StackGeometry.relative(
        float(state.get("relative_stack_range", 500)),
        abs(float(state["step_size"])),
        flipped=bool(
            stage_config.get(f"flip_{state.get('primary_z_axis', 'z')}", False)
        ),
        start_focus=float(state.get("relative_start_focus", 0)) if ramp else 0,
        end_focus=float(state.get("relative_end_focus", 0)) if ramp else 0,
    )


def freeze_relative_stack(model: Model) -> RelativeStackPlan:
    """Read a stopped stage and validate all references before camera preparation.

    Parameters
    ----------
    model : Model
        Model running in its hardware worker, with idle polling suspended by the
        caller. This function must never run on the Tk thread.

    Returns
    -------
    RelativeStackPlan
        Immutable geometry and position-table snapshot for this acquisition.
    """
    configuration = model.configuration
    microscope = model.active_microscope
    if configuration is None or microscope is None:
        raise RuntimeError(
            "A microscope must be loaded before acquiring a relative stack"
        )
    state = configuration["experiment"]["MicroscopeState"]
    name = state["microscope_name"]
    if name != model.active_microscope_name:
        raise ValueError("The selected microscope must be active before acquiring")
    stage_config = configuration["configuration"]["microscopes"][name]["stage"]
    geometry = relative_geometry(state, stage_config)
    z_axis, f_axis = state.get("primary_z_axis", "z"), state.get("primary_f_axis", "f")
    if z_axis == f_axis:
        raise ValueError("Relative stacks require distinct Z-stack and focus axes")
    if not {z_axis, f_axis}.issubset(microscope.stages):
        raise ValueError("The selected stack axes must be available on this microscope")
    model.stop_stage()
    # Do not allow partial replies to inherit coordinates from the position cache.
    current = model.get_stage_position(require_fresh=True)
    try:
        reference = StackReference(
            float(current[f"{z_axis}_pos"]), float(current[f"{f_axis}_pos"])
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Cannot read the relative stack reference position") from error
    if not all(isfinite(v) for v in (reference.z, reference.focus)):
        raise ValueError("Relative stack reference positions must be finite")
    try:
        if not all(
            isfinite(float(current[f"{axis}_pos"])) for axis in microscope.stages
        ):
            raise ValueError("Nonfinite stage position")
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "A complete, finite stage readback is required for a relative stack"
        ) from error
    headers: tuple[str, ...] = ()
    positions: tuple[tuple[float, ...], ...] = ()
    references = [reference]
    if state["is_multiposition"]:
        table = configuration["multi_positions"]
        headers = tuple(table[0])
        positions = tuple(tuple(float(v) for v in row) for row in table[1:])
        if not positions or any(
            len(row) != len(headers) or not all(map(isfinite, row)) for row in positions
        ):
            raise ValueError(
                "Relative stacks require a complete, finite position table"
            )
        required = {axis.upper() for axis in microscope.stages}
        if not required.issubset(headers):
            raise ValueError("The position table is missing an active stage axis")
        zi, fi = headers.index(z_axis.upper()), headers.index(f_axis.upper())
        references = [StackReference(row[zi], row[fi]) for row in positions]

    def check(axis: str, value: float) -> None:
        if not isfinite(value):
            raise ValueError(f"Relative stack target for {axis} must be finite")
        if not configuration["experiment"]["StageParameters"].get("limits", True):
            return
        lower, upper = stage_config.get(f"{axis}_min"), stage_config.get(f"{axis}_max")
        if (lower is not None and value < float(lower)) or (
            upper is not None and value > float(upper)
        ):
            raise ValueError(
                f"Relative stack target {value:g} exceeds {axis} stage limits"
            )

    defocus = [
        float(channel.get("defocus", 0))
        for channel in state["channels"].values()
        if channel["is_selected"]
    ]
    first_defocus = defocus[0] if defocus else 0.0
    secondary = state.get("secondary_stack_settings", {})
    if not set(secondary.keys()).issubset(microscope.stages):
        raise ValueError(
            "A secondary stacking axis is not available on this microscope"
        )
    for row in positions:
        for axis in set(microscope.stages) - {z_axis, f_axis} - set(secondary.keys()):
            check(axis, row[headers.index(axis.upper())])
    for ref in references:
        for offset in (geometry.z.start, geometry.z.end):
            check(z_axis, ref.z + offset)
            for axis, distance in state.get("secondary_stack_settings", {}).items():
                check(axis, ref.z + offset + float(distance))
        for offset in (geometry.focus.start, geometry.focus.end):
            for channel_defocus in defocus or [0.0]:
                check(f_axis, (offset - first_defocus) + ref.focus + channel_defocus)
    plan = RelativeStackPlan(
        name, z_axis, f_axis, geometry, reference, headers, positions
    )
    state.update(plan.legacy_fields())
    model.event_queue.put(
        (
            "stack_reference",
            {
                "microscope_name": name,
                "z": reference.z,
                "focus": reference.focus,
                "multiposition": bool(positions),
            },
        )
    )
    return plan
