import pytest

from navigate.controller.sub_controllers.gui_settings_popup import (
    coerce_gui_value,
    flatten_gui_settings,
    gui_setting_minimum,
    is_boolean_gui_setting,
    is_integer_gui_setting,
    is_nonnegative_gui_setting,
    is_step_size_gui_setting,
    gui_setting_group,
)


def test_flatten_gui_settings_lists_nested_settings():
    settings = {
        "channel_settings": {"count": 5},
        "theme": {"palette": {"accent": "#4b78b8"}},
        "histogram": {"enabled": True},
    }

    assert flatten_gui_settings(settings) == [
        ("channel_settings.count", "5"),
        ("histogram.enabled", "True"),
    ]


@pytest.mark.parametrize(
    ("entered_value", "path", "expected_value"),
    [
        ("6", ("channel_settings", "count"), 6),
        ("500", ("time", "timepoints", "max"), 500),
        ("0.0001", ("stack_acquisition", "step_size", "step"), 0.0001),
        ("0.25", ("time", "stack_pause", "step"), 0.25),
    ],
)
def test_coerce_gui_value_uses_the_setting_type(entered_value, path, expected_value):
    assert coerce_gui_value(entered_value, path) == expected_value


def test_setting_type_helpers_identify_integer_and_boolean_settings():
    assert is_integer_gui_setting(("channel_settings", "count"))
    assert is_integer_gui_setting(("time", "timepoints", "step"))
    assert not is_integer_gui_setting(("time", "stack_pause", "step"))
    assert is_boolean_gui_setting(("histogram", "enabled"))
    assert is_boolean_gui_setting(("mip_display", "enabled"))


def test_gui_setting_lower_bound_rules():
    assert is_step_size_gui_setting(("stack_acquisition", "step_size", "step"))
    assert is_step_size_gui_setting(("galvo_waveform", "amplitude_step_size"))
    assert gui_setting_minimum(("channel_settings", "count")) == "1"
    assert gui_setting_minimum(("time", "stack_pause", "min")) == "0"
    assert gui_setting_minimum(("galvo_waveform", "offset_step_size")) == "0"
    assert is_nonnegative_gui_setting(("channel_settings", "laser_power", "min"))
    assert is_nonnegative_gui_setting(("channel_settings", "exposure_time", "max"))
    assert is_nonnegative_gui_setting(("channel_settings", "interval", "step"))
    assert is_nonnegative_gui_setting(("stack_acquisition", "step_size", "max"))


@pytest.mark.parametrize(
    ("value", "path", "message"),
    [
        ("0", ("channel_settings", "count"), "greater than 0"),
        ("0", ("stack_acquisition", "step_size", "step"), "greater than 0"),
        ("0", ("galvo_waveform", "amplitude_step_size"), "greater than 0"),
        ("-1", ("time", "stack_pause", "min"), "greater than or equal to 0"),
        (
            "-1",
            ("channel_settings", "laser_power", "min"),
            "greater than or equal to 0",
        ),
        (
            "-1",
            ("channel_settings", "exposure_time", "max"),
            "greater than or equal to 0",
        ),
        (
            "-1",
            ("channel_settings", "interval", "step"),
            "greater than 0",
        ),
        (
            "-1",
            ("stack_acquisition", "step_size", "min"),
            "greater than or equal to 0",
        ),
    ],
)
def test_coerce_gui_value_rejects_invalid_lower_bounds(value, path, message):
    with pytest.raises(ValueError, match=message):
        coerce_gui_value(value, path)


def test_gui_setting_group_uses_the_top_level_configuration_section():
    assert gui_setting_group(("channel_settings", "laser_power", "step")) == (
        "Channel Settings"
    )
    assert gui_setting_group(("mip_display", "enabled")) == "Mip Display"
    assert gui_setting_group(("remote_focus_waveform", "amplitude_step_size")) == (
        "Remote Focus Waveform"
    )
    assert gui_setting_group(("galvo_waveform", "offset_step_size")) == (
        "Galvo Waveform"
    )
