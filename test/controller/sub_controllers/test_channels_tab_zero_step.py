"""Regression tests for z-stack step validation."""

from types import SimpleNamespace

from navigate.controller.sub_controllers.channels_tab import ChannelsTabController


class Value:
    """Minimal value holder matching the Tk variable interface."""

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_update_z_steps_rejects_zero_when_configured_minimum_is_zero():
    """A custom GUI configuration cannot expose division by zero."""
    controller = ChannelsTabController.__new__(ChannelsTabController)
    controller.in_initialization = False
    controller.stack_acq_vals = {
        "start_position": Value(0),
        "end_position": Value(10),
        "step_size": Value(0),
        "number_z_steps": Value(1),
    }
    controller.stack_acq_widgets = {
        "step_size": SimpleNamespace(widget=SimpleNamespace(cget=lambda _option: 0.0))
    }
    controller.microscope_state_dict = {"abs_z_start": 1, "abs_z_end": 1}

    controller.update_z_steps()

    assert controller.stack_acq_vals["number_z_steps"].get() == 0
    assert controller.microscope_state_dict["abs_z_start"] == 0
    assert controller.microscope_state_dict["abs_z_end"] == 0
