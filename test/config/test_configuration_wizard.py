from copy import deepcopy

import pytest

from navigate.config.configuration_wizard import (
    ADVANCED_IMPORTANCE,
    BASIC_IMPORTANCE,
    DEFAULT_STEP,
    collect_step_warnings,
    device_type_changed,
    field_applies_to_device,
    field_is_visible,
    get_field_metadata,
    get_steps,
    merge_loaded_and_edited_values,
)


def test_get_steps_uses_metadata_order_and_fallback():
    widgets = {
        "hardware/type": ["Device Type", "Combobox", "string", {}, None],
        "serial": ["Serial", "Input", "string", None, None],
        "frame_config": {"ref": "hardware"},
    }
    metadata = {
        "steps": ["Device Type", "Connection"],
        "fields": {
            "hardware/type": {"step": "Device Type"},
            "serial": {"step": "Connection"},
        },
    }

    assert get_steps(widgets, metadata) == ["Device Type", "Connection"]
    assert get_steps(widgets, {}) == [DEFAULT_STEP]


def test_get_field_metadata_falls_back_to_default_step():
    metadata = {"fields": {"serial": {"step": "Connection", "importance": "required"}}}

    assert get_field_metadata(metadata, "serial") == {
        "step": "Connection",
        "importance": "required",
    }
    assert get_field_metadata(metadata, "missing") == {
        "step": DEFAULT_STEP,
        "importance": "recommended",
    }


def test_field_applies_to_device_without_rule_is_visible():
    assert field_applies_to_device({}, "Virtual Device")
    assert field_applies_to_device({"applies_to": ["Virtual Device"]}, "Virtual Device")
    assert not field_applies_to_device(
        {"applies_to": ["Photometrics Iris 15B"]}, "Virtual Device"
    )


@pytest.mark.parametrize("importance", sorted(BASIC_IMPORTANCE))
def test_basic_mode_shows_required_and_recommended_fields(importance):
    assert field_is_visible(
        field_key="delay",
        widget_spec=["Delay", "Spinbox", "float", {}, None],
        field_metadata={"step": "Timing", "importance": importance},
        selected_step="Timing",
        advanced_mode=False,
        selected_device="Virtual Device",
    )


@pytest.mark.parametrize("importance", sorted(ADVANCED_IMPORTANCE))
def test_basic_mode_hides_optional_and_advanced_fields(importance):
    assert not field_is_visible(
        field_key="camera_connection",
        widget_spec=["Camera Connection", "Input", "string", None, None],
        field_metadata={
            "step": "Connection",
            "importance": importance,
            "applies_to": ["Photometrics Iris 15B"],
        },
        selected_step="Connection",
        advanced_mode=False,
        selected_device="Virtual Device",
    )


def test_advanced_mode_shows_device_specific_fields_on_matching_step():
    assert field_is_visible(
        field_key="camera_connection",
        widget_spec=["Camera Connection", "Input", "string", None, None],
        field_metadata={
            "step": "Connection",
            "importance": "advanced",
            "applies_to": ["Photometrics Iris 15B"],
        },
        selected_step="Connection",
        advanced_mode=True,
        selected_device="Virtual Device",
    )


def test_field_visibility_honors_selected_step():
    assert not field_is_visible(
        field_key="delay",
        widget_spec=["Delay", "Spinbox", "float", {}, None],
        field_metadata={"step": "Timing", "importance": "recommended"},
        selected_step="Connection",
        advanced_mode=True,
        selected_device="Virtual Device",
    )


def test_collect_step_warnings_reports_missing_required_values():
    widgets = {
        "hardware/type": ["Device Type", "Combobox", "string", {}, None],
        "sample_rate": ["Sample Rate", "Input", "int", None, None],
    }
    metadata = {
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "sample_rate": {"step": "Timing", "importance": "required"},
        }
    }
    values = {"hardware/type": "National Instruments", "sample_rate": ""}

    assert collect_step_warnings(widgets, metadata, values) == {
        "Timing": ["Sample Rate is required."]
    }


def test_merge_loaded_and_edited_values_preserves_hidden_values_without_type_change():
    loaded = {
        "hardware": {
            "type": "Photometrics",
            "serial_number": "302352",
            "camera_connection": "USB",
        },
        "delay": 10,
    }
    edited = {"hardware": {"type": "Photometrics"}, "delay": 12}

    result = merge_loaded_and_edited_values(
        loaded_block=loaded,
        edited_block=edited,
        device_type_changed=False,
    )

    assert result == {
        "hardware": {
            "type": "Photometrics",
            "serial_number": "302352",
            "camera_connection": "USB",
        },
        "delay": 12,
    }


def test_merge_loaded_and_edited_values_drops_loaded_values_after_type_change():
    loaded = {"hardware": {"type": "Photometrics", "camera_connection": "USB"}}
    edited = {"hardware": {"type": "Synthetic"}}

    result = merge_loaded_and_edited_values(
        loaded_block=deepcopy(loaded),
        edited_block=deepcopy(edited),
        device_type_changed=True,
    )

    assert result == edited


def test_device_type_changed_reads_nested_device_type():
    loaded = {"hardware": {"type": "Photometrics"}}
    edited = {"hardware": {"type": "Synthetic"}}

    assert device_type_changed(loaded, edited, "hardware/type")
    assert not device_type_changed(loaded, loaded, "hardware/type")


def test_device_type_changed_handles_missing_loaded_value():
    edited = {"hardware": {"type": "Synthetic"}}

    assert not device_type_changed(None, edited, "hardware/type")
