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
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Preload and repair Navigate configuration before device startup."""

# Standard Library Imports
from dataclasses import dataclass, field
from pathlib import Path
import copy
import logging
from multiprocessing.managers import DictProxy, ListProxy
from typing import Any, Optional

# Third Party Imports
import yaml

# Local Imports
from navigate.config.config import (
    update_config_dict,
    verify_configuration,
    verify_experiment_config,
    verify_positions_config,
    verify_waveform_constants,
)
from navigate.config.device_schema import (
    category_base_class_name,
    get_configuration_schema,
)
from navigate.model.devices.configuration_schema import CollectionSpec, SettingSpec
from navigate.tools.common_functions import load_param_from_module

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

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


@dataclass(frozen=True)
class PreloadChange:
    """A user-facing in-memory configuration repair."""

    path: str
    rule: str
    message: str


@dataclass(frozen=True)
class PreloadIssue:
    """A preload issue that may prevent Navigate from starting."""

    path: str
    rule: str
    message: str
    fatal: bool = False


@dataclass
class PreloadReport:
    """Structured record of in-memory preload repairs and issues."""

    changes: list[PreloadChange] = field(default_factory=list)
    issues: list[PreloadIssue] = field(default_factory=list)
    debug_changes: list[PreloadChange] = field(default_factory=list)

    @property
    def fatal_issues(self) -> list[PreloadIssue]:
        """Return fatal issues collected during preload."""
        return [issue for issue in self.issues if issue.fatal]

    @property
    def has_fatal_issues(self) -> bool:
        """Return whether preload collected any fatal issue."""
        return bool(self.fatal_issues)

    def add_change(self, path: str, rule: str, message: str) -> None:
        """Record a user-facing configuration repair."""
        self.changes.append(PreloadChange(path, rule, message))

    def add_debug_change(self, path: str, rule: str, message: str) -> None:
        """Record a non-user-facing compatibility repair."""
        self.debug_changes.append(PreloadChange(path, rule, message))

    def add_issue(
        self, path: str, rule: str, message: str, *, fatal: bool = False
    ) -> None:
        """Record a preload issue."""
        self.issues.append(PreloadIssue(path, rule, message, fatal))


class PreloadError(Exception):
    """Raised when preload cannot repair configuration safely."""

    def __init__(self, report: PreloadReport):
        self.report = report
        messages = "; ".join(issue.message for issue in report.fatal_issues)
        super().__init__(messages or "Navigate configuration preload failed.")


def preload_configuration(
    manager,
    configuration,
    *,
    is_synthetic: bool = False,
    multi_positions: Optional[Any] = None,
) -> PreloadReport:
    """Repair in-memory configuration before Navigate starts devices."""
    report = PreloadReport()

    _record_silent_legacy_repairs(configuration, report)
    _apply_microscope_inheritance(manager, configuration)
    _add_missing_required_devices(manager, configuration, report)

    try:
        verify_configuration(manager, configuration)
    except Exception as error:
        report.add_issue(
            "configuration",
            "legacy-verification",
            str(error),
            fatal=True,
        )
        _log_report(report)
        raise PreloadError(report) from error

    _validate_device_schemas(manager, configuration, report, is_synthetic=is_synthetic)
    if report.has_fatal_issues:
        _log_report(report)
        raise PreloadError(report)

    verify_experiment_config(manager, configuration)
    verify_waveform_constants(manager, configuration)

    if multi_positions is not None:
        configuration["multi_positions"] = verify_positions_config(multi_positions)

    _log_report(report)
    return report


def _log_report(report: PreloadReport) -> None:
    """Log preload changes and issues without storing them in configuration."""
    for change in report.changes:
        logger.info("Preload repaired %s: %s", change.path, change.message)
    for change in report.debug_changes:
        logger.debug("Preload compatibility repair %s: %s", change.path, change.message)
    for issue in report.issues:
        log = logger.error if issue.fatal else logger.warning
        log("Preload issue %s: %s", issue.path, issue.message)


def _record_silent_legacy_repairs(configuration, report: PreloadReport) -> None:
    """Apply deceased-name repairs that should not appear in the user report."""
    device_config = configuration["configuration"]["microscopes"]
    for microscope_name in list(device_config.keys()):
        microscope_config = device_config[microscope_name]
        if "lasers" in microscope_config and "laser" not in microscope_config:
            microscope_config["laser"] = microscope_config.pop("lasers")
            report.add_debug_change(
                f"configuration.microscopes.{microscope_name}.laser",
                "legacy-rename",
                "Renamed deceased lasers key to laser.",
            )


def _apply_microscope_inheritance(manager, configuration) -> None:
    """Apply the current ``Child (Parent)`` microscope inheritance rule."""
    device_config = configuration["configuration"]["microscopes"]
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


def _add_missing_required_devices(
    manager, configuration, report: PreloadReport
) -> None:
    """Add synthetic defaults for missing required device sections."""
    synthetic_devices = _synthetic_device_templates()
    device_config = configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in device_config.items():
        for category in REQUIRED_DEVICE_CATEGORIES:
            if not _missing_device_section(microscope_config.get(category)):
                continue
            update_config_dict(
                manager,
                microscope_config,
                category,
                copy.deepcopy(synthetic_devices[category]),
            )
            report.add_change(
                f"configuration.microscopes.{microscope_name}.{category}",
                "missing-required-device",
                f"Added synthetic {category} device because it was missing.",
            )


def _missing_device_section(value: Any) -> bool:
    """Return whether a required device section is absent or empty."""
    if value is None:
        return True
    if isinstance(value, (dict, DictProxy)):
        return len(value) == 0
    if isinstance(value, (list, ListProxy)):
        return len(value) == 0
    return False


def _synthetic_device_templates() -> dict[str, Any]:
    """Return per-device synthetic templates from the bundled synthetic config."""
    synthetic_path = Path(__file__).resolve().parent / "synthetic_configuration.yaml"
    with open(synthetic_path) as synthetic_file:
        synthetic_config = yaml.load(synthetic_file, Loader=yaml.FullLoader)
    microscope = synthetic_config["microscopes"]["Mesoscale"]
    return {
        category: copy.deepcopy(microscope[category])
        for category in REQUIRED_DEVICE_CATEGORIES
    }


def _validate_device_schemas(
    manager,
    configuration,
    report: PreloadReport,
    *,
    is_synthetic: bool,
) -> None:
    """Fill required schema defaults and report missing required properties."""
    microscopes = configuration["configuration"]["microscopes"]
    for microscope_name, microscope_config in microscopes.items():
        for category, device in _iter_schema_devices(microscope_config):
            schema_targets = []
            resolved = _resolve_schema_target(category, device)
            if resolved is not None:
                schema_targets.append(resolved)
            if is_synthetic:
                synthetic_target = ("synthetic", _synthetic_class_name(category))
                if synthetic_target not in schema_targets:
                    schema_targets.append(synthetic_target)

            for manufacturer, model in schema_targets:
                try:
                    schema = get_configuration_schema(category, manufacturer, model)
                except (FileNotFoundError, SyntaxError, AttributeError, ImportError):
                    continue
                _repair_required_schema_settings(
                    manager,
                    report,
                    device,
                    schema,
                    path_prefix=(
                        f"configuration.microscopes.{microscope_name}.{category}"
                    ),
                )


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
) -> None:
    """Repair or report missing required settings from a schema."""
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
        if not isinstance(spec, SettingSpec) or not spec.required:
            continue

        found, value = _get_path(device, name, with_found=True)
        if not found or not _value_is_present(value):
            if spec.default is not None:
                _set_path(manager, device, name, spec.default)
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

        normalized = _normalize_setting_value(value, spec)
        if normalized is _INVALID_VALUE:
            if spec.default is not None:
                _set_path(manager, device, name, spec.default)
                report.add_change(
                    f"{path_prefix}.{name.replace('/', '.')}",
                    "schema-invalid-default",
                    f"Replaced invalid setting {name} with schema default.",
                )
            else:
                report.add_issue(
                    f"{path_prefix}.{name.replace('/', '.')}",
                    "schema-invalid-value",
                    f"Required setting {name} is invalid and has no default.",
                    fatal=True,
                )
        elif normalized != value:
            _set_path(manager, device, name, normalized)
            report.add_change(
                f"{path_prefix}.{name.replace('/', '.')}",
                "schema-type-normalized",
                f"Normalized required setting {name} to {spec.value_type.__name__}.",
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
    device_type = _device_type_for_schema(category, device)
    if not isinstance(device_type, str) or not device_type:
        return None
    if device_type.lower().startswith("synthetic"):
        return "synthetic", _synthetic_class_name(category)

    if "." in device_type:
        manufacturer, model = device_type.split(".")[:2]
        return manufacturer, _ensure_class_name(category, model)

    try:
        device_types = load_param_from_module(
            "navigate.config.configuration_database", category + "_device_types"
        )
    except (ImportError, AttributeError, ModuleNotFoundError):
        device_types = {}

    for display_name, value in device_types.items():
        if isinstance(value, tuple):
            model, manufacturer = value
        else:
            model, manufacturer = value, str(value).lower()
        if device_type in {display_name, model}:
            return str(manufacturer).lower(), _ensure_class_name(category, str(model))

    return None


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
