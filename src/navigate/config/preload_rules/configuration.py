# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:
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

# Standard Library Imports
import copy
import logging
import uuid
from pathlib import Path
from typing import Any, Optional
from multiprocessing.managers import DictProxy, ListProxy

import yaml

from navigate.config.config import update_config_dict
from navigate.config.device_schema import (
    category_base_class_name,
    canonical_device_type,
    get_configuration_schema,
)
from navigate.config.device_refs import DEVICE_REFERENCE_FIELDS
from navigate.config.preload import PreloadContext, PreloadRule, PreloadReport
from navigate.model.devices.configuration_schema import CollectionSpec, SettingSpec
from navigate.tools.common_functions import build_ref_name, load_param_from_module

logger = logging.getLogger(__name__.split(".")[1])

REQUIRED_DEVICE_CATEGORIES = (
    "daq",
    "camera",
    "shutter",
    "remote_focus",
    "galvo",
    "stage",
    "laser",
    "zoom",
)

REQUIRED_STAGE_AXES = ("x", "y", "z", "f", "theta")


def record_silent_legacy_repairs(context: PreloadContext) -> None:
    """Apply deceased-name repairs that should not appear in the user report."""
    device_config = context.configuration["configuration"]["microscopes"]
    for microscope_name in list(device_config.keys()):
        microscope_config = device_config[microscope_name]
        if (
            "remote_focus_device" in microscope_config
            and "remote_focus" not in microscope_config
        ):
            microscope_config["remote_focus"] = microscope_config.pop(
                "remote_focus_device"
            )
            context.report.add_debug_change(
                f"configuration.microscopes.{microscope_name}.remote_focus",
                "legacy-rename",
                "Renamed deceased remote_focus_device key to remote_focus.",
            )
        if "lasers" in microscope_config and "laser" not in microscope_config:
            microscope_config["laser"] = microscope_config.pop("lasers")
            context.report.add_debug_change(
                f"configuration.microscopes.{microscope_name}.laser",
                "legacy-rename",
                "Renamed deceased lasers key to laser.",
            )
        _repair_deceased_stage_type_names(context, microscope_name, microscope_config)


def apply_microscope_inheritance(context: PreloadContext) -> None:
    """Apply the current ``Child (Parent)`` microscope inheritance rule."""
    manager = context.manager
    device_config = context.configuration["configuration"]["microscopes"]
    microscope_name_seq = []
    inherited_microscope_dict = {}
    microscope_names_list = list(device_config.keys())
    for microscope_name in microscope_names_list:
        try:
            parenthesis_l = microscope_name.index("(")
        except ValueError:
            if microscope_name.strip() not in microscope_name_seq:
                microscope_name_seq.append(microscope_name.strip())
            continue

        if ")" not in microscope_name[parenthesis_l + 1 :]:
            microscope_name_seq.append(microscope_name.strip())
            continue

        parenthesis_r = microscope_name[parenthesis_l + 1 :].index(")")
        parent_microscope_name = microscope_name[
            parenthesis_l + 1 : parenthesis_l + parenthesis_r + 1
        ].strip()

        if parent_microscope_name not in microscope_name_seq:
            microscope_name_seq.append(parent_microscope_name)

        idx = microscope_name_seq.index(parent_microscope_name)
        child_microscope_name = microscope_name[:parenthesis_l].strip()
        microscope_name_seq.insert(idx + 1, child_microscope_name)
        inherited_microscope_dict[child_microscope_name] = parent_microscope_name
        child_config = device_config.pop(microscope_name)
        if isinstance(child_config, DictProxy):
            device_config[child_microscope_name] = child_config
        else:
            update_config_dict(
                manager, device_config, child_microscope_name, child_config
            )

    for microscope_name in microscope_name_seq:
        if microscope_name not in inherited_microscope_dict:
            continue
        parent_microscope_name = inherited_microscope_dict[microscope_name]
        if parent_microscope_name not in device_config:
            logger.error(
                "Microscope %s is not defined in configuration.yaml",
                parent_microscope_name,
            )
            raise Exception(
                f"Microscope {parent_microscope_name} is not defined "
                f"in configuration.yaml"
            )

        for device_name in device_config[parent_microscope_name].keys():
            if device_name not in device_config[microscope_name].keys():
                device_config[microscope_name][device_name] = device_config[
                    parent_microscope_name
                ][device_name]


def add_missing_required_devices(context: PreloadContext) -> None:
    """Add synthetic defaults for missing required device sections."""
    synthetic_devices = _synthetic_device_templates()
    device_config = context.configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in device_config.items():
        for category in REQUIRED_DEVICE_CATEGORIES:
            if not _missing_device_section(microscope_config.get(category)):
                continue
            update_config_dict(
                context.manager,
                microscope_config,
                category,
                copy.deepcopy(synthetic_devices[category]),
            )
            context.report.add_change(
                f"configuration.microscopes.{microscope_name}.{category}",
                "missing-required-device",
                f"Added synthetic {category} device because it was missing.",
            )


def normalize_laser_hardware(context: PreloadContext) -> None:
    """Generate the unified laser hardware section used by runtime startup."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_config in microscopes.values():
        laser_config = microscope_config.get("laser")
        if not isinstance(laser_config, (list, ListProxy)):
            continue
        for laser in laser_config:
            if not isinstance(laser, (dict, DictProxy)):
                continue
            onoff_hardware = _get_path(laser, "onoff/hardware") or {}
            power_hardware = _get_path(laser, "power/hardware") or {}
            onoff_type = (
                onoff_hardware.get("type", "Synthetic")
                if isinstance(onoff_hardware, (dict, DictProxy))
                else "Synthetic"
            )
            power_type = (
                power_hardware.get("type", "Synthetic")
                if isinstance(power_hardware, (dict, DictProxy))
                else "Synthetic"
            )
            if onoff_type != "Synthetic":
                hardware_config = dict(onoff_hardware)
            elif power_type != "Synthetic":
                hardware_config = dict(power_hardware)
            else:
                hardware_config = {"type": "Synthetic"}
            hardware_config["wavelength"] = laser.get("wavelength")
            update_config_dict(context.manager, laser, "hardware", hardware_config)


def ensure_zoom_hardware(context: PreloadContext) -> None:
    """Ensure zoom has a hardware section and type before schema/reference checks."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_config in microscopes.values():
        zoom_config = microscope_config.get("zoom")
        if not isinstance(zoom_config, (dict, DictProxy)):
            continue
        hardware = zoom_config.get("hardware")
        if not isinstance(hardware, (dict, DictProxy)):
            update_config_dict(
                context.manager,
                zoom_config,
                "hardware",
                {"type": "Synthetic", "servo_id": 0},
            )
        elif "type" not in hardware:
            hardware["type"] = "Synthetic"


def ensure_zoom_calibration(context: PreloadContext) -> None:
    """Ensure zoom position and pixel-size maps are startup-safe."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in microscopes.items():
        zoom_config = microscope_config.get("zoom")
        if not isinstance(zoom_config, (dict, DictProxy)):
            continue

        position = zoom_config.get("position")
        if not isinstance(position, (dict, DictProxy)) or len(position) == 0:
            update_config_dict(
                context.manager,
                zoom_config,
                "position",
                {"N/A": 0},
            )
            position = zoom_config["position"]

        pixel_size = zoom_config.get("pixel_size")
        if not isinstance(pixel_size, (dict, DictProxy)) or len(pixel_size) == 0:
            update_config_dict(
                context.manager,
                zoom_config,
                "pixel_size",
                {zoom_name: 1.0 for zoom_name in position.keys()},
            )
            pixel_size = zoom_config["pixel_size"]

        for zoom_name in position.keys():
            if zoom_name in pixel_size:
                continue
            pixel_size[zoom_name] = 1.0
            context.report.add_issue(
                (
                    f"configuration.microscopes.{microscope_name}."
                    f"zoom.pixel_size.{zoom_name}"
                ),
                "zoom-pixel-size-default",
                (
                    f"Zoom position '{zoom_name}' did not have a matching "
                    "pixel_size entry; added default pixel_size 1.0."
                ),
                fatal=False,
            )

        stage_positions = zoom_config.get("stage_positions")
        if isinstance(stage_positions, (dict, DictProxy)) and len(stage_positions) == 0:
            zoom_config.pop("stage_positions", None)


def ensure_required_stage_axes(context: PreloadContext) -> None:
    """Add one synthetic stage hardware entry for required axes not yet covered."""
    synthetic_stage = _synthetic_device_templates()["stage"]["hardware"][0]
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in microscopes.items():
        stage_config = microscope_config.get("stage")
        if not isinstance(stage_config, (dict, DictProxy)):
            continue
        stage_hardware = stage_config.get("hardware")
        if not isinstance(stage_hardware, (dict, DictProxy, list, ListProxy)):
            continue

        stage_entries = (
            list(stage_hardware)
            if isinstance(stage_hardware, (list, ListProxy))
            else [stage_hardware]
        )
        configured_axes = {
            axis.casefold()
            for stage in stage_entries
            for axis in _stage_axes(stage.get("axes") if hasattr(stage, "get") else [])
        }
        missing_axes = [
            axis
            for axis in REQUIRED_STAGE_AXES
            if axis.casefold() not in configured_axes
        ]
        if not missing_axes:
            continue

        missing_stage = copy.deepcopy(synthetic_stage)
        missing_stage["axes"] = missing_axes
        missing_stage["axes_mapping"] = []
        missing_stage["serial_number"] = _default_reference_value(
            "stage", "serial_number", len(stage_entries)
        )

        update_config_dict(
            context.manager,
            stage_config,
            "hardware",
            [dict(stage) for stage in stage_entries] + [missing_stage],
        )
        context.report.add_change(
            f"configuration.microscopes.{microscope_name}.stage.hardware",
            "missing-stage-axes",
            "Added synthetic stage hardware for missing axes: "
            + ", ".join(missing_axes),
        )


def clean_stage_coupled_axes(context: PreloadContext) -> None:
    """Remove coupled-axis pairs that reference axes missing from the microscope."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_config in microscopes.values():
        stage_config = microscope_config.get("stage")
        if not isinstance(stage_config, (dict, DictProxy)):
            continue
        coupled_axes = stage_config.get("coupled_axes")
        if not isinstance(coupled_axes, (dict, DictProxy)):
            continue

        available_axes = _combined_stage_axes(stage_config)
        valid_pairs = {
            leader: follower
            for leader, follower in coupled_axes.items()
            if str(leader).casefold() in available_axes
            and str(follower).casefold() in available_axes
        }
        if valid_pairs:
            update_config_dict(
                context.manager, stage_config, "coupled_axes", valid_pairs
            )
        else:
            stage_config.pop("coupled_axes", None)


def clean_stage_joystick_axes(context: PreloadContext) -> None:
    """Remove joystick axes that are missing from the microscope stage axes."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_config in microscopes.values():
        stage_config = microscope_config.get("stage")
        if not isinstance(stage_config, (dict, DictProxy)):
            continue
        joystick_axes = stage_config.get("joystick_axes")
        if not isinstance(joystick_axes, (list, ListProxy, tuple, str)):
            continue

        available_axes = _combined_stage_axes(stage_config)
        valid_axes = [
            axis
            for axis in _stage_axes(joystick_axes)
            if str(axis).casefold() in available_axes
        ]
        if valid_axes:
            update_config_dict(
                context.manager, stage_config, "joystick_axes", valid_axes
            )
        else:
            stage_config.pop("joystick_axes", None)


def normalize_filter_wheels(context: PreloadContext) -> None:
    """Normalize filter-wheel shape and assign stable unique display names."""
    microscopes = context.configuration["configuration"]["microscopes"]
    reference_names = []
    reference_configs = []
    used_names = set()

    for microscope_name, microscope_config in microscopes.items():
        filter_wheel_config = microscope_config.get("filter_wheel")
        if filter_wheel_config is None:
            continue
        if isinstance(filter_wheel_config, (dict, DictProxy)):
            update_config_dict(
                context.manager,
                microscope_config,
                "filter_wheel",
                [dict(filter_wheel_config)],
            )
            filter_wheel_config = microscope_config["filter_wheel"]
        if not isinstance(filter_wheel_config, (list, ListProxy)):
            continue

        for wheel_config in filter_wheel_config:
            if not isinstance(wheel_config, (dict, DictProxy)):
                continue
            hardware = wheel_config.get("hardware", {})
            if not isinstance(hardware, (dict, DictProxy)):
                continue
            _ensure_filter_wheel_available_filters(
                context, microscope_name, wheel_config, hardware
            )
            wheel_ref = build_ref_name(
                "-",
                hardware.get("type"),
                hardware.get("wheel_number"),
            )
            if wheel_ref not in reference_names:
                reference_names.append(wheel_ref)
                reference_configs.append(wheel_config)
                if (
                    wheel_config.get("name") is None
                    and hardware.get("name") is not None
                ):
                    wheel_config["name"] = hardware["name"]

            reference_config = reference_configs[reference_names.index(wheel_ref)]
            if reference_config.get("name") is not None:
                wheel_config["name"] = reference_config["name"]
            elif wheel_config.get("name") is not None:
                reference_config["name"] = wheel_config["name"]
            elif hardware.get("name") is not None:
                reference_config["name"] = hardware["name"]

            if reference_config.get("name") is not None:
                if reference_config["name"] in used_names:
                    reference_config["name"] = None
                else:
                    used_names.add(reference_config["name"])

    for index, wheel_config in enumerate(reference_configs):
        if wheel_config.get("name") is not None:
            continue
        name = _next_filter_wheel_name(used_names)
        wheel_config["name"] = name
        used_names.add(name)

    if not reference_configs:
        return
    for microscope_config in microscopes.values():
        filter_wheel_config = microscope_config.get("filter_wheel")
        if not isinstance(filter_wheel_config, (list, ListProxy)):
            continue
        for wheel_config in filter_wheel_config:
            hardware = wheel_config.get("hardware", {})
            if not isinstance(hardware, (dict, DictProxy)):
                continue
            wheel_ref = build_ref_name(
                "-",
                hardware.get("type"),
                hardware.get("wheel_number"),
            )
            if wheel_ref in reference_names:
                wheel_config["name"] = reference_configs[
                    reference_names.index(wheel_ref)
                ]["name"]


def _ensure_filter_wheel_available_filters(
    context: PreloadContext, microscope_name: str, wheel_config, hardware
) -> None:
    """Validate available filter definitions for one filter wheel."""
    available_filters = wheel_config.get("available_filters")
    if (
        not isinstance(available_filters, (dict, DictProxy))
        or len(available_filters) == 0
    ):
        if context.is_synthetic or _is_synthetic_type(hardware.get("type")):
            update_config_dict(
                context.manager,
                wheel_config,
                "available_filters",
                {"Empty": 0},
            )
            context.report.add_issue(
                f"configuration.microscopes.{microscope_name}.filter_wheel.available_filters",
                "filter-wheel-default-filter",
                "Filter wheel had no available filters; added default Empty: 0.",
                fatal=False,
            )
        else:
            context.report.add_issue(
                f"configuration.microscopes.{microscope_name}.filter_wheel.available_filters",
                "filter-wheel-missing-filters",
                "Filter wheel must define at least one available filter.",
                fatal=True,
            )
        return

    if not _is_ni_type(hardware.get("type")):
        return
    for filter_name, channel in available_filters.items():
        if isinstance(channel, str) and "/" in channel:
            continue
        context.report.add_issue(
            (
                f"configuration.microscopes.{microscope_name}."
                f"filter_wheel.available_filters.{filter_name}"
            ),
            "filter-wheel-invalid-ni-channel",
            f"A valid channel must be given for the filter name {filter_name}.",
            fatal=True,
        )


def _is_synthetic_type(device_type: object) -> bool:
    """Return whether a config type token identifies a synthetic device."""
    return isinstance(device_type, str) and any(
        part.casefold().startswith("synthetic") for part in device_type.split(".")
    )


def _is_ni_type(device_type: object) -> bool:
    """Return whether a config type token identifies an NI device."""
    normalized_type = canonical_device_type("filter_wheel", device_type)
    return normalized_type == "ni.NI" or device_type == "NI"


def _repair_deceased_stage_type_names(
    context: PreloadContext, microscope_name: str, microscope_config
) -> None:
    """Apply deceased stage model names without user-facing report entries."""
    stage_config = microscope_config.get("stage")
    if not isinstance(stage_config, (dict, DictProxy)):
        return
    hardware_config = stage_config.get("hardware")
    if isinstance(hardware_config, (list, ListProxy)):
        stages = hardware_config
    elif isinstance(hardware_config, (dict, DictProxy)):
        stages = [hardware_config]
    else:
        return

    try:
        deceased_names = load_param_from_module(
            "navigate.config.configuration_database", "deceased_device_type_names"
        )
    except (ImportError, AttributeError, ModuleNotFoundError):
        return
    for index, stage in enumerate(stages):
        stage_type = stage.get("type") if hasattr(stage, "get") else None
        if stage_type not in deceased_names:
            continue
        stage["type"] = deceased_names[stage_type]
        context.report.add_debug_change(
            (
                f"configuration.microscopes.{microscope_name}."
                f"stage.hardware[{index}].type"
            ),
            "legacy-device-type",
            f"Renamed deceased stage type {stage_type}.",
        )


def _next_filter_wheel_name(used_names: set[str]) -> str:
    """Return the next default filter-wheel name not already used."""
    index = 0
    while True:
        name = f"FilterWheel-{index}"
        if name not in used_names:
            return name
        index += 1


def _combined_stage_axes(stage_config) -> set[str]:
    """Return all configured stage axes for one microscope as lower-case tokens."""
    hardware_config = stage_config.get("hardware")
    if isinstance(hardware_config, (list, ListProxy)):
        stages = hardware_config
    elif isinstance(hardware_config, (dict, DictProxy)):
        stages = [hardware_config]
    else:
        stages = []
    return {
        axis.casefold()
        for stage in stages
        for axis in _stage_axes(stage.get("axes") if hasattr(stage, "get") else [])
    }


def _stage_axes(value: Any) -> list[str]:
    """Return stage axes from list-shaped or simple string configuration values."""
    if isinstance(value, (list, ListProxy, tuple)):
        return [str(axis) for axis in value]
    if isinstance(value, str):
        return [
            axis.strip().strip("'\"")
            for axis in value.strip().strip("[]").split(",")
            if axis.strip()
        ]
    return []


def validate_device_schemas(context: PreloadContext) -> None:
    """Fill required schema defaults and report missing required properties."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in microscopes.items():
        for category, device in _iter_schema_devices(microscope_config):
            if context.is_synthetic:
                schema_targets = [("synthetic", _synthetic_class_name(category))]
                report_defaults = False
            else:
                schema_targets = []
                resolved = _resolve_schema_target(category, device)
                if resolved is not None:
                    schema_targets.append(resolved)
                report_defaults = True

            for manufacturer, model in schema_targets:
                try:
                    schema = get_configuration_schema(category, manufacturer, model)
                except (FileNotFoundError, SyntaxError, AttributeError, ImportError):
                    continue
                _repair_required_schema_settings(
                    context.manager,
                    context.report,
                    device,
                    schema,
                    path_prefix=(
                        f"configuration.microscopes.{microscope_name}.{category}"
                    ),
                    report_defaults=report_defaults,
                )


def normalize_device_type_names(context: PreloadContext) -> None:
    """Normalize startup device types to ``manufacturer.model`` tokens."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in microscopes.items():
        for category, device, index in _iter_type_devices(microscope_config):
            hardware = device.get("hardware") if hasattr(device, "get") else None
            if not isinstance(hardware, (dict, DictProxy)):
                continue
            current_type = hardware.get("type")
            normalized_type = canonical_device_type(category, current_type)
            if normalized_type is None or normalized_type == current_type:
                continue
            hardware["type"] = normalized_type
            context.report.add_change(
                (
                    f"configuration.microscopes.{microscope_name}."
                    f"{category}[{index}].hardware.type"
                ),
                "device-type-normalized",
                (
                    f"Normalized {category} device type from {current_type} "
                    f"to {normalized_type}."
                ),
            )


def ensure_device_reference_fields(context: PreloadContext) -> None:
    """Ensure each configured device can build its startup reference name."""
    microscopes = context.configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in microscopes.items():
        for category, device, index in _iter_reference_devices(microscope_config):
            hardware = (
                device
                if category == "stage"
                else device.get("hardware") if hasattr(device, "get") else None
            )
            if not isinstance(hardware, (dict, DictProxy)):
                continue
            for field_name in DEVICE_REFERENCE_FIELDS.get(category, ()):
                if _value_is_present(hardware.get(field_name)):
                    continue
                if _reference_field_is_schema_required(
                    category,
                    device,
                    field_name,
                    is_synthetic=context.is_synthetic,
                ):
                    context.report.add_issue(
                        (
                            f"configuration.microscopes.{microscope_name}."
                            f"{category}.hardware.{field_name}"
                        ),
                        "device-reference-required",
                        (
                            f"Device reference field {field_name} is missing for "
                            f"{category} and is required by the device schema."
                        ),
                        fatal=True,
                    )
                    continue
                hardware[field_name] = _default_reference_value(
                    category,
                    field_name,
                    index,
                    existing_values=_existing_reference_values(
                        microscope_config, category, field_name
                    ),
                )
        _warn_duplicate_device_references(context, microscope_name, microscope_config)


def _missing_device_section(value: Any) -> bool:
    """Return whether a required device section is absent or empty."""
    if value is None:
        return True
    if isinstance(value, (dict, DictProxy)):
        return len(value) == 0
    if isinstance(value, (list, ListProxy)):
        return len(value) == 0
    return False


def _iter_reference_devices(microscope_config) -> list[tuple[str, Any, int]]:
    """Return device dictionaries that use shared reference-name fields."""
    devices = []
    for category in DEVICE_REFERENCE_FIELDS:
        if category not in microscope_config:
            continue
        value = microscope_config[category]
        if category == "stage":
            hardware = value.get("hardware", []) if hasattr(value, "get") else []
            if isinstance(hardware, (list, ListProxy)):
                devices.extend(
                    (category, item, index) for index, item in enumerate(hardware)
                )
            elif isinstance(hardware, (dict, DictProxy)):
                devices.append((category, hardware, 0))
            continue
        if isinstance(value, (list, ListProxy)):
            devices.extend((category, item, index) for index, item in enumerate(value))
        else:
            devices.append((category, value, 0))
    return devices


def _iter_type_devices(microscope_config) -> list[tuple[str, Any, int]]:
    """Return top-level device dictionaries whose hardware type can be normalized."""
    devices = []
    for category in DEVICE_REFERENCE_FIELDS:
        if category == "stage":
            continue
        if category not in microscope_config:
            continue
        value = microscope_config[category]
        if isinstance(value, (list, ListProxy)):
            devices.extend((category, item, index) for index, item in enumerate(value))
        else:
            devices.append((category, value, 0))
    return devices


def _reference_field_is_schema_required(
    category: str, device, field_name: str, *, is_synthetic: bool = False
) -> bool:
    """Return whether a reference field is required by the resolved schema."""
    resolved = (
        ("synthetic", _synthetic_class_name(category))
        if is_synthetic
        else _resolve_schema_target(category, device)
    )
    if resolved is None:
        return True
    try:
        schema = get_configuration_schema(category, *resolved)
    except (FileNotFoundError, SyntaxError, AttributeError, ImportError):
        return True

    for schema_name in _reference_schema_names(field_name):
        spec = schema.get(schema_name)
        if isinstance(spec, SettingSpec) and spec.required:
            return True
    return False


def _reference_schema_names(field_name: str) -> tuple[str, str]:
    """Return possible schema paths for a startup reference field."""
    return f"hardware/{field_name}", field_name


def _existing_reference_values(
    microscope_config, category: str, field_name: str
) -> set[Any]:
    """Return present reference-field values under one microscope/category."""
    values = set()
    for item_category, device, _ in _iter_reference_devices(microscope_config):
        if item_category != category:
            continue
        hardware = (
            device
            if category == "stage"
            else device.get("hardware") if hasattr(device, "get") else None
        )
        if isinstance(hardware, (dict, DictProxy)) and _value_is_present(
            hardware.get(field_name)
        ):
            values.add(hardware[field_name])
    return values


def _warn_duplicate_device_references(
    context: PreloadContext, microscope_name: str, microscope_config
) -> None:
    """Report duplicate startup reference names under each device category."""
    seen_references = {}
    for category, device, index in _iter_reference_devices(microscope_config):
        hardware = (
            device
            if category == "stage"
            else device.get("hardware") if hasattr(device, "get") else None
        )
        if not isinstance(hardware, (dict, DictProxy)):
            continue
        reference_fields = DEVICE_REFERENCE_FIELDS.get(category, ())
        if not all(
            _value_is_present(hardware.get(field)) for field in reference_fields
        ):
            continue
        reference_value = build_ref_name(
            "_", *(hardware.get(field) for field in reference_fields)
        )
        key = (category, reference_value)
        if key not in seen_references:
            seen_references[key] = index
            continue
        context.report.add_issue(
            (f"configuration.microscopes.{microscope_name}." f"{category}[{index}]"),
            "duplicate-device-reference",
            (
                f"Duplicate {category} reference '{reference_value}' also appears "
                f"at index {seen_references[key]}; only the first one will be loaded."
            ),
            fatal=False,
        )


def _default_reference_value(
    category: str,
    field_name: str,
    index: int,
    *,
    existing_values: Optional[set[Any]] = None,
) -> Any:
    """Return a deterministic silent value for an optional reference field."""
    if field_name in {"wheel_number", "servo_id"}:
        return _next_unused_integer(existing_values or set(), index)
    if field_name == "wavelength":
        return 488 + index
    if category == "stage" and field_name == "serial_number":
        return f"stage_{uuid.uuid4().hex[:8]}"
    if field_name == "type":
        return "Synthetic"
    return f"{category}_{index}"


def _next_unused_integer(existing_values: set[Any], start: int) -> int:
    """Return the first integer >= start not present in existing values."""
    used_values = set()
    for value in existing_values:
        try:
            used_values.add(int(value))
        except (TypeError, ValueError):
            continue
    candidate = start
    while candidate in used_values:
        candidate += 1
    return candidate


def _synthetic_device_templates() -> dict[str, Any]:
    """Return per-device synthetic templates from the bundled synthetic config."""
    synthetic_path = (
        Path(__file__).resolve().parent.parent / "synthetic_configuration.yaml"
    )
    with open(synthetic_path) as synthetic_file:
        synthetic_config = yaml.load(synthetic_file, Loader=yaml.FullLoader)
    microscope = synthetic_config["microscopes"]["Mesoscale"]
    return {
        category: copy.deepcopy(microscope[category])
        for category in REQUIRED_DEVICE_CATEGORIES
    }


def _iter_schema_devices(microscope_config) -> list[tuple[str, Any]]:
    """Return device dictionaries paired with their schema category."""
    devices = []
    for category in REQUIRED_DEVICE_CATEGORIES:
        if category not in microscope_config:
            continue
        value = microscope_config[category]
        if category == "stage":
            hardware = value.get("hardware", []) if hasattr(value, "get") else []
            if isinstance(hardware, (list, ListProxy)):
                devices.extend((category, item) for item in hardware)
            elif isinstance(hardware, (dict, DictProxy)):
                devices.append((category, hardware))
        elif category in {"galvo", "laser"}:
            if isinstance(value, (list, ListProxy)):
                devices.extend((category, item) for item in value)
            else:
                devices.append((category, value))
        else:
            devices.append((category, value))
    return devices


def _repair_required_schema_settings(
    manager,
    report: PreloadReport,
    device,
    schema: dict[str, object],
    *,
    path_prefix: str,
    report_defaults: bool = True,
) -> None:
    """Repair or report schema settings that can prevent successful startup."""
    for name, spec in schema.items():
        if isinstance(spec, CollectionSpec):
            if spec.minimum_items and _collection_size(_get_path(device, name)) < (
                spec.minimum_items
            ):
                report.add_issue(
                    f"{path_prefix}.{name.replace('/', '.')}",
                    "schema-required-collection",
                    f"Required collection {name} has fewer than "
                    f"{spec.minimum_items} items.",
                    fatal=True,
                )
            continue
        if not isinstance(spec, SettingSpec):
            continue

        found, value = _get_path(device, name, with_found=True)
        if not found or not _value_is_present(value):
            if not spec.required:
                continue
            elif spec.default is not None:
                _set_path(manager, device, name, spec.default)
                if report_defaults:
                    report.add_change(
                        f"{path_prefix}.{name.replace('/', '.')}",
                        "schema-required-default",
                        f"Added missing required setting {name} from schema default.",
                    )
            else:
                report.add_issue(
                    f"{path_prefix}.{name.replace('/', '.')}",
                    "schema-required-missing",
                    f"Required setting {name} is missing and has no default.",
                    fatal=True,
                )
            continue

        if name.endswith("hardware/type"):
            continue
        if not spec.required and (not report_defaults or spec.choices is None):
            continue

        normalized = _normalize_setting_value(value, spec)
        if normalized is _INVALID_VALUE:
            if spec.default is not None:
                _set_path(manager, device, name, spec.default)
                if spec.required:
                    report.add_change(
                        f"{path_prefix}.{name.replace('/', '.')}",
                        "schema-invalid-default",
                        f"Replaced invalid setting {name} with schema default.",
                    )
                else:
                    report.add_issue(
                        f"{path_prefix}.{name.replace('/', '.')}",
                        "schema-optional-invalid-default",
                        (
                            f"Optional setting {name} was invalid and was replaced "
                            "with the schema default."
                        ),
                        fatal=False,
                    )
            else:
                if spec.required:
                    report.add_issue(
                        f"{path_prefix}.{name.replace('/', '.')}",
                        "schema-invalid-value",
                        f"Required setting {name} is invalid and has no default.",
                        fatal=True,
                    )
                else:
                    _delete_path(device, name)
                    report.add_issue(
                        f"{path_prefix}.{name.replace('/', '.')}",
                        "schema-optional-invalid-removed",
                        (
                            f"Optional setting {name} was invalid and had no schema "
                            "default, so it was removed."
                        ),
                        fatal=False,
                    )
        elif normalized != value:
            _set_path(manager, device, name, normalized)
            report.add_change(
                f"{path_prefix}.{name.replace('/', '.')}",
                "schema-type-normalized",
                f"Normalized setting {name} to {spec.value_type.__name__}.",
            )


def _collection_size(value: Any) -> int:
    """Return collection size, treating absent and scalar values as empty."""
    if isinstance(value, (dict, DictProxy, list, ListProxy)):
        return len(value)
    return 0


def _get_path(target, path: str, *, with_found: bool = False):
    """Read a slash-delimited path from a mapping."""
    current = target
    for part in path.split("/"):
        if not isinstance(current, (dict, DictProxy)) or part not in current:
            return (False, None) if with_found else None
        current = current[part]
    return (True, current) if with_found else current


def _set_path(manager, target, path: str, value: Any) -> None:
    """Set a slash-delimited path in a shared mapping."""
    parts = path.split("/")
    current = target
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], (dict, DictProxy)):
            update_config_dict(manager, current, part, {})
        current = current[part]
    if isinstance(value, (dict, list)):
        update_config_dict(manager, current, parts[-1], copy.deepcopy(value))
    else:
        current[parts[-1]] = value


def _delete_path(target, path: str) -> None:
    """Delete a slash-delimited path from a mapping if it exists."""
    parts = path.split("/")
    current = target
    for part in parts[:-1]:
        if not isinstance(current, (dict, DictProxy)) or part not in current:
            return
        current = current[part]
    if isinstance(current, (dict, DictProxy)):
        current.pop(parts[-1], None)


def _value_is_present(value: Any) -> bool:
    """Return whether a required schema value is present."""
    return value is not None and value != "" and value != []


class _InvalidValue:
    """Sentinel for invalid schema values."""


_INVALID_VALUE = _InvalidValue()


def _normalize_setting_value(value: Any, spec: SettingSpec) -> Any:
    """Normalize a value to the schema type, or return an invalid sentinel."""
    if spec.value_type in {str, int, float, bool} and isinstance(
        value, (dict, DictProxy, list, ListProxy)
    ):
        return value

    try:
        if spec.value_type is bool:
            if isinstance(value, bool):
                normalized = value
            elif isinstance(value, str) and value.strip().casefold() in {
                "true",
                "false",
            }:
                normalized = value.strip().casefold() == "true"
            else:
                return _INVALID_VALUE
        else:
            normalized = spec.value_type(value)
    except (TypeError, ValueError):
        return _INVALID_VALUE

    if spec.choices is not None and normalized not in spec.choices:
        return _INVALID_VALUE
    if spec.minimum is not None and normalized < spec.minimum:
        return _INVALID_VALUE
    if spec.maximum is not None and normalized > spec.maximum:
        return _INVALID_VALUE
    return normalized


def _resolve_schema_target(category: str, device) -> Optional[tuple[str, str]]:
    """Resolve a config device into ``(manufacturer, class_name)`` for schema lookup."""
    device_type = canonical_device_type(
        category, _device_type_for_schema(category, device)
    )
    if not isinstance(device_type, str) or not device_type or "." not in device_type:
        return None
    if device_type.lower().startswith("synthetic"):
        return "synthetic", _synthetic_class_name(category)

    manufacturer, model = device_type.split(".")[:2]
    return manufacturer, _ensure_class_name(category, model)


def _device_type_for_schema(category: str, device) -> Optional[str]:
    """Return the hardware type used to resolve a device schema."""
    if not isinstance(device, (dict, DictProxy)):
        return None
    if category == "stage":
        return device.get("type")
    if category == "laser":
        power_type = _get_path(device, "power/hardware/type")
        onoff_type = _get_path(device, "onoff/hardware/type")
        return power_type or onoff_type
    hardware = device.get("hardware")
    if isinstance(hardware, (dict, DictProxy)):
        return hardware.get("type")
    return None


def _synthetic_class_name(category: str) -> str:
    """Return the synthetic class name for a device category."""
    suffix = category_base_class_name(category).removesuffix("Base")
    return "Synthetic" + suffix


def _ensure_class_name(category: str, model: str) -> str:
    """Convert a model token into the concrete class name used for schema lookup."""
    suffix = category_base_class_name(category).removesuffix("Base")
    if model.endswith(suffix):
        return model
    return model + suffix


CONFIGURATION_RULES = [
    PreloadRule(
        "configuration",
        "legacy_device_names",
        record_silent_legacy_repairs,
    ),
    PreloadRule(
        "configuration",
        "microscope_inheritance",
        apply_microscope_inheritance,
    ),
    PreloadRule(
        "configuration",
        "missing_required_devices",
        add_missing_required_devices,
    ),
    PreloadRule(
        "configuration",
        "laser_hardware",
        normalize_laser_hardware,
    ),
    PreloadRule(
        "configuration",
        "zoom_hardware",
        ensure_zoom_hardware,
    ),
    PreloadRule(
        "configuration",
        "zoom_calibration",
        ensure_zoom_calibration,
    ),
    PreloadRule(
        "configuration",
        "required_stage_axes",
        ensure_required_stage_axes,
    ),
    PreloadRule(
        "configuration",
        "stage_coupled_axes",
        clean_stage_coupled_axes,
    ),
    PreloadRule(
        "configuration",
        "stage_joystick_axes",
        clean_stage_joystick_axes,
    ),
    PreloadRule(
        "configuration",
        "filter_wheels",
        normalize_filter_wheels,
    ),
    PreloadRule(
        "configuration",
        "device_schema_validation",
        validate_device_schemas,
        stop_on_fatal=True,
    ),
    PreloadRule(
        "configuration",
        "device_type_names",
        normalize_device_type_names,
    ),
    PreloadRule(
        "configuration",
        "device_reference_fields",
        ensure_device_reference_fields,
        stop_on_fatal=True,
    ),
]
