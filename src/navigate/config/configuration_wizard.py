"""Helpers for the configuration assistant mini-wizard UI."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_STEP = "Details"
BASIC_IMPORTANCE = {"required", "recommended"}
ADVANCED_IMPORTANCE = {"optional", "advanced"}
NON_FIELD_WIDGET_TYPES = {"Button", "Label"}


def get_field_metadata(metadata: dict[str, Any], field_key: str) -> dict[str, Any]:
    """Return metadata for a field, with conservative defaults."""
    fields = metadata.get("fields", {})
    field_metadata = fields.get(field_key, {})
    return {
        "step": field_metadata.get("step", DEFAULT_STEP),
        "importance": field_metadata.get("importance", "recommended"),
        **field_metadata,
    }


def get_steps(widgets: dict[str, list[Any]], metadata: dict[str, Any]) -> list[str]:
    """Return ordered wizard steps for a hardware tab."""
    configured_steps = metadata.get("steps", [])
    if configured_steps:
        return list(configured_steps)

    steps = []
    for field_key, widget_spec in widgets.items():
        if field_key == "frame_config":
            continue
        if widget_spec[1] in NON_FIELD_WIDGET_TYPES:
            continue
        step = get_field_metadata(metadata, field_key)["step"]
        if step not in steps:
            steps.append(step)
    return steps or [DEFAULT_STEP]


def field_applies_to_device(
    field_metadata: dict[str, Any],
    selected_device: str | None,
) -> bool:
    """Return whether a metadata rule applies to the selected device label."""
    applies_to = field_metadata.get("applies_to")
    if not applies_to or not selected_device:
        return True
    return selected_device in applies_to


def field_is_visible(
    *,
    field_key: str,
    widget_spec: list[Any],
    field_metadata: dict[str, Any],
    selected_step: str,
    advanced_mode: bool,
    selected_device: str | None,
) -> bool:
    """Return whether a field should be visible for the current wizard state."""
    if field_key == "frame_config":
        return False
    if widget_spec[1] in NON_FIELD_WIDGET_TYPES:
        return True
    if field_metadata.get("step", DEFAULT_STEP) != selected_step:
        return False
    if advanced_mode:
        return True
    if field_metadata.get("importance", "recommended") not in BASIC_IMPORTANCE:
        return False
    return field_applies_to_device(field_metadata, selected_device)


def _display_name(widget_spec: list[Any], field_key: str) -> str:
    if widget_spec and widget_spec[0]:
        return str(widget_spec[0])
    return field_key.replace("/", " ").replace("_", " ").title()


def collect_step_warnings(
    widgets: dict[str, list[Any]],
    metadata: dict[str, Any],
    values: dict[str, Any],
) -> dict[str, list[str]]:
    """Return required-field warnings grouped by wizard step."""
    warnings: dict[str, list[str]] = {}
    for field_key, widget_spec in widgets.items():
        if field_key == "frame_config":
            continue
        if widget_spec[1] in NON_FIELD_WIDGET_TYPES:
            continue
        field_metadata = get_field_metadata(metadata, field_key)
        if field_metadata.get("importance") != "required":
            continue
        value = values.get(field_key)
        if value is None or str(value).strip() == "":
            step = field_metadata.get("step", DEFAULT_STEP)
            warnings.setdefault(step, []).append(
                f"{_display_name(widget_spec, field_key)} is required."
            )
    return warnings


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        elif isinstance(value, list) and isinstance(result.get(key), list):
            result[key] = _deep_merge_list(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _deep_merge_list(base: list[Any], overlay: list[Any]) -> list[Any]:
    result = []
    for index, value in enumerate(overlay):
        base_value = base[index] if index < len(base) else None
        if isinstance(value, dict) and isinstance(base_value, dict):
            result.append(_deep_merge(base_value, value))
        else:
            result.append(deepcopy(value))
    return result


def nested_get(data: dict[str, Any] | None, path: str) -> Any:
    """Return a nested value using slash-separated configurator paths."""
    if not data:
        return None
    current: Any = data
    for part in path.split("/"):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            if not current or not isinstance(current[0], dict):
                return None
            current = current[0].get(part)
        else:
            return None
        if current is None:
            return None
    return current


def _list_backed_field_values(
    block: dict[str, Any],
    device_field: str,
) -> list[Any] | None:
    if "/" in device_field:
        list_path, field_path = device_field.rsplit("/", 1)
    else:
        list_path = "hardware"
        field_path = device_field

    list_value = nested_get(block, list_path)
    if not isinstance(list_value, list):
        return None

    values = []
    for item in list_value:
        if not isinstance(item, dict):
            return None
        value = nested_get(item, field_path)
        if value is None:
            return None
        values.append(value)
    return values


def _device_field_values(block: dict[str, Any], device_field: str) -> list[Any] | None:
    values = _list_backed_field_values(block, device_field)
    if values is not None:
        return values

    value = nested_get(block, device_field)
    if value is None and "/" not in device_field:
        value = nested_get(block, f"hardware/{device_field}")
    if value is None:
        return None
    return [value]


def device_type_changed(
    loaded_block: dict[str, Any] | None,
    edited_block: dict[str, Any],
    device_field: str | None,
) -> bool:
    """Return whether a hardware block changed device type during editing."""
    if not loaded_block or not device_field:
        return False
    loaded_values = _device_field_values(loaded_block, device_field)
    edited_values = _device_field_values(edited_block, device_field)
    if loaded_values is None or edited_values is None:
        return False
    return any(
        loaded_value != edited_value
        for loaded_value, edited_value in zip(loaded_values, edited_values)
    )


def merge_loaded_and_edited_values(
    *,
    loaded_block: dict[str, Any] | None,
    edited_block: dict[str, Any],
    device_type_changed: bool,
) -> dict[str, Any]:
    """Merge visible edits with loaded hidden values."""
    if device_type_changed or not loaded_block:
        return deepcopy(edited_block)
    return _deep_merge(loaded_block, edited_block)
