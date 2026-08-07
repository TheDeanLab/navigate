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
#

# Standard library imports
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

# Third party imports
import pytest
import numpy as np

# Local application imports
from navigate.controller.sub_controllers import AutofocusPopupController
from navigate.view.popups.autofocus_setting_popup import AutofocusPopup
from navigate.view.theme import get_theme_color


class TestAutofocusPopupController:
    """Class for testing autofocus popup controller

    Methods
    -------
    test_init()
        Tests that the controller is initialized correctly
    test_attr()
        Tests that the attributes are initialized correctly
    test_populate_experiment_values()
        Tests that the values are populated correctly
    test_update_experiment_values()
        Tests that the values are updated correctly
    test_start_autofocus()
        Tests that the start autofocus function works correctly
    test_display_plot()
        Tests that the display plot function works correctly
    """

    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        """Setup for testing autofocus popup controller

        Parameters
        ----------
        dummy_controller : DummyController
            Dummy controller for testing

        """
        autofocus_popup = AutofocusPopup(dummy_controller.view)
        self.autofocus_controller = AutofocusPopupController(
            autofocus_popup, dummy_controller
        )

    def test_init(self):
        """Tests that the controller is initialized correctly

        Raises
        ------
        AssertionError
            If the controller is not initialized correctly
        """
        assert isinstance(self.autofocus_controller, AutofocusPopupController)
        assert self.autofocus_controller.view.popup.winfo_exists() == 1

    def test_scan_parameters_reserve_inline_bounds_warning_row(self):
        warning_label = self.autofocus_controller.view.bounds_warning_label

        assert self.autofocus_controller.view.bounds_warning_var.get() == ""
        assert int(warning_label.grid_info()["row"]) == 3
        assert int(warning_label.grid_info()["columnspan"]) == 3
        assert str(warning_label.cget("foreground")) == get_theme_color(
            "danger", "red"
        )

    def configure_focus_bounds(self, minimum=0, maximum=1000, enabled=True):
        parent = self.autofocus_controller.parent_controller
        parent.configuration["experiment"]["StageParameters"]["f"] = 0
        parent.configuration["experiment"]["StageParameters"]["limits"] = enabled
        parent.configuration_controller.get_stage_position_limits = MagicMock(
            side_effect=lambda suffix: {
                "f": minimum if suffix == "_min" else maximum
            }
        )
        settings = self.autofocus_controller.setting_dict[
            self.autofocus_controller.microscope_name
        ]["stage"]["f"]
        settings.update(
            {
                "coarse_selected": True,
                "coarse_range": 500,
                "coarse_step_size": 50,
                "fine_selected": False,
                "fine_range": 50,
                "fine_step_size": 5,
            }
        )
        for key, value in settings.items():
            if key in self.autofocus_controller.view.setting_vars:
                self.autofocus_controller.view.setting_vars[key].set(value)
        return settings

    def test_refresh_bounds_validation_marks_and_clears_coarse_range(self):
        self.configure_focus_bounds()

        errors = self.autofocus_controller.refresh_bounds_validation()

        expected = (
            "The requested coarse scan (-250 to 250 µm) exceeds the focus-stage "
            "limits (0 to 1000 µm)."
        )
        assert errors == [expected]
        assert self.autofocus_controller.view.bounds_warning_var.get() == expected
        coarse_range = self.autofocus_controller.widgets["coarse_range"].widget
        fine_range = self.autofocus_controller.widgets["fine_range"].widget
        assert str(coarse_range.cget("foreground")) == get_theme_color(
            "danger", "red"
        )
        assert str(fine_range.cget("foreground")) == get_theme_color(
            "text", "black"
        )

        self.autofocus_controller.parent_controller.configuration["experiment"][
            "StageParameters"
        ]["f"] = 500
        assert self.autofocus_controller.refresh_bounds_validation() == []
        assert self.autofocus_controller.view.bounds_warning_var.get() == ""
        assert str(coarse_range.cget("foreground")) == get_theme_color(
            "text", "black"
        )

    def test_refresh_bounds_validation_checks_fine_only(self):
        settings = self.configure_focus_bounds()
        settings.update(
            {
                "coarse_selected": False,
                "fine_selected": True,
                "fine_range": 50,
                "fine_step_size": 5,
            }
        )
        self.autofocus_controller.view.setting_vars["coarse_selected"].set(False)
        self.autofocus_controller.view.setting_vars["fine_selected"].set(True)

        errors = self.autofocus_controller.refresh_bounds_validation()

        assert errors == [
            "The requested fine scan (-25 to 25 µm) exceeds the focus-stage "
            "limits (0 to 1000 µm)."
        ]

    def test_refresh_bounds_validation_does_not_guess_combined_fine_center(self):
        settings = self.configure_focus_bounds()
        self.autofocus_controller.parent_controller.configuration["experiment"][
            "StageParameters"
        ]["f"] = 500
        settings.update(
            {
                "coarse_selected": True,
                "coarse_range": 100,
                "coarse_step_size": 10,
                "fine_selected": True,
                "fine_range": 5000,
                "fine_step_size": 50,
            }
        )
        for key in (
            "coarse_selected",
            "coarse_range",
            "coarse_step_size",
            "fine_selected",
            "fine_range",
            "fine_step_size",
        ):
            self.autofocus_controller.view.setting_vars[key].set(settings[key])

        assert self.autofocus_controller.refresh_bounds_validation() == []

    def test_refresh_bounds_validation_ignores_disabled_limits(self):
        self.configure_focus_bounds(enabled=False)

        assert self.autofocus_controller.refresh_bounds_validation() == []

    def test_start_autofocus_blocks_invalid_bounds_with_final_dialog(self):
        self.configure_focus_bounds()
        parent = self.autofocus_controller.parent_controller

        with patch.object(parent, "execute") as execute, patch(
            "navigate.controller.sub_controllers.autofocus.messagebox.showerror"
        ) as showerror:
            self.autofocus_controller.start_autofocus()

        execute.assert_not_called()
        showerror.assert_called_once_with(
            title="Navigate",
            message=(
                "The requested coarse scan (-250 to 250 µm) exceeds the "
                "focus-stage limits (0 to 1000 µm)."
            ),
        )

    def test_stop_acquisition_button_matches_start_button(self):
        """The popup exposes an equally emphasized acquisition stop control."""
        start_button = self.autofocus_controller.view.autofocus_btn
        stop_button = self.autofocus_controller.view.stop_acquisition_btn

        assert start_button["text"] == "▶ Start Autofocus"
        assert stop_button["text"] == "■ Stop Acquisition"
        assert start_button["style"] == "Accent.TButton"
        assert stop_button["style"] == "Accent.TButton"
        assert int(start_button["width"]) == int(stop_button["width"])
        assert str(start_button["state"]) == "normal"
        assert str(stop_button["state"]) == "disabled"

    @pytest.mark.parametrize(
        ("state", "autofocus_active", "mode", "start_state", "stop_state"),
        [
            ("idle", False, "live", "normal", "disabled"),
            ("starting", True, "live", "disabled", "disabled"),
            ("running", False, "live", "normal", "normal"),
            ("running", True, "live", "disabled", "normal"),
            ("running", False, "z-stack", "disabled", "normal"),
            ("stopping", True, "live", "disabled", "disabled"),
        ],
    )
    def test_acquisition_state_controls_buttons(
        self,
        monkeypatch,
        state,
        autofocus_active,
        mode,
        start_state,
        stop_state,
    ):
        """Acquisition and autofocus state expose only valid popup actions."""
        parent_controller = self.autofocus_controller.parent_controller
        monkeypatch.setattr(
            parent_controller,
            "acquire_bar_controller",
            SimpleNamespace(
                is_acquiring=state != "idle",
                mode=mode,
            ),
            raising=False,
        )
        start_button = self.autofocus_controller.view.autofocus_btn
        stop_button = self.autofocus_controller.view.stop_acquisition_btn

        self.autofocus_controller.set_acquisition_state(state)
        self.autofocus_controller.set_autofocus_state(autofocus_active)

        assert str(start_button["state"]) == start_state
        assert str(stop_button["state"]) == stop_state

    def test_stop_acquisition_uses_global_stop_route(self, monkeypatch):
        """Popup cancellation follows the same route as the main Stop button."""
        parent_controller = self.autofocus_controller.parent_controller
        parent_controller.clear()
        acquire_button = parent_controller.view.acquire_bar.acquire_btn
        original_state = str(acquire_button["state"])
        monkeypatch.setattr(
            parent_controller,
            "acquire_bar_controller",
            SimpleNamespace(
                is_acquiring=True,
                mode="live",
                view=SimpleNamespace(acquire_btn=acquire_button),
            ),
            raising=False,
        )

        try:
            self.autofocus_controller.set_acquisition_state("running")
            self.autofocus_controller.set_autofocus_state(True)
            self.autofocus_controller.view.stop_acquisition_btn.invoke()

            assert parent_controller.pop() == "stop_acquire"
            assert (
                str(self.autofocus_controller.view.autofocus_btn["state"]) == "disabled"
            )
            assert (
                str(self.autofocus_controller.view.stop_acquisition_btn["state"])
                == "disabled"
            )
            assert str(acquire_button["state"]) == "disabled"
        finally:
            acquire_button.configure(state=original_state)
            parent_controller.clear()

    def test_attr(self):
        """Tests that the attributes are initialized correctly

        Raises
        ------
        AssertionError
            If the attributes are not initialized correctly
        """

        # Listing off attributes to check existence
        attrs = [
            "autofocus_fig",
            "autofocus_coarse",
            "widgets",
            "setting_dict",
        ]

        for attr in attrs:
            assert hasattr(self.autofocus_controller, attr)

    def test_populate_experiment_values(self):
        """Tests that the values are populated correctly

        Raises
        ------
        AssertionError
            If the values are not populated correctly
        """
        microscope_name = self.autofocus_controller.microscope_name
        device = self.autofocus_controller.widgets["device"].get()
        device_ref = self.autofocus_controller.widgets["device_ref"].get()
        for k in self.autofocus_controller.widgets:
            if k not in (
                "device",
                "device_ref",
                "target_channel",
                "calibration_action",
            ):
                assert self.autofocus_controller.widgets[k].get() == str(
                    self.autofocus_controller.setting_dict[microscope_name][device][
                        device_ref
                    ][k]
                )
            # Some values are ints but Tkinter only uses strings

    def test_update_experiment_values(self):
        """Tests that the values are updated correctly

        Raises
        ------
        AssertionError
            If the values are not updated correctly
        """
        # Changing values
        self.autofocus_controller.widgets["coarse_range"].set(200)
        self.autofocus_controller.widgets["coarse_step_size"].set(30)
        self.autofocus_controller.view.setting_vars["coarse_selected"].set(False)
        self.autofocus_controller.widgets["fine_range"].set(25)
        self.autofocus_controller.widgets["fine_step_size"].set(2)
        self.autofocus_controller.view.setting_vars["fine_selected"].set(False)

        microscope_name = self.autofocus_controller.microscope_name
        device = self.autofocus_controller.widgets["device"].get()
        device_ref = self.autofocus_controller.widgets["device_ref"].get()

        # Checking values match
        for k in self.autofocus_controller.widgets:
            if k not in (
                "device",
                "device_ref",
                "target_channel",
                "calibration_action",
            ):
                assert self.autofocus_controller.widgets[k].get() == str(
                    self.autofocus_controller.setting_dict[microscope_name][device][
                        device_ref
                    ][k]
                )
        for k in self.autofocus_controller.view.setting_vars:
            assert (
                self.autofocus_controller.view.setting_vars[k].get()
                == self.autofocus_controller.setting_dict[microscope_name][device][
                    device_ref
                ][k]
            )

    def test_start_autofocus(self):
        """Tests that the start autofocus function works correctly

        Raises
        ------
        AssertionError
            If the start autofocus function does not work correctly
        """

        # Calling function
        self.autofocus_controller.start_autofocus()

        # Checking message sent
        res = self.autofocus_controller.parent_controller.pop()
        assert res == "autofocus"

    def test_start_autofocus_passes_channel_and_calibration_action(self):
        self.autofocus_controller.widgets["target_channel"].set("CH2")
        self.autofocus_controller.widgets["calibration_action"].set("Capture Reference")

        with patch.object(
            self.autofocus_controller.parent_controller, "execute"
        ) as execute:
            self.autofocus_controller.start_autofocus()

            device = self.autofocus_controller.widgets["device"].get()
            device_ref = self.autofocus_controller.widgets["device_ref"].get()
            execute.assert_called_with(
                "autofocus",
                device,
                device_ref,
                "channel_2",
                "capture_reference",
                "channel_2",
                False,
            )

    def test_auto_defocus_warning_uses_clear_acquisition_instruction(self, monkeypatch):
        """Auto Defocus clearly instructs users to stop acquisition first."""
        parent_controller = self.autofocus_controller.parent_controller
        monkeypatch.setattr(
            parent_controller,
            "acquire_bar_controller",
            SimpleNamespace(is_acquiring=True),
            raising=False,
        )
        self.autofocus_controller.widgets["calibration_action"].set("Auto Defocus")

        with patch(
            "navigate.controller.sub_controllers.autofocus.messagebox.showwarning"
        ) as showwarning:
            self.autofocus_controller.start_autofocus()

        showwarning.assert_called_once_with(
            title="Navigate",
            message=("Please stop the acquisition before calculating defocus values."),
        )

    def test_target_channel_uses_channel_setting_labels(self):
        channel_values = tuple(
            self.autofocus_controller.widgets["target_channel"].widget["values"]
        )
        channel_keys = tuple(
            self.autofocus_controller.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["channels"].keys()
        )
        expected_values = tuple(
            f"CH{channel_key.removeprefix('channel_')}" for channel_key in channel_keys
        )

        assert channel_values == expected_values
        assert self.autofocus_controller.widgets["target_channel"].get() == (
            expected_values[0]
        )

    def test_handle_autofocus_complete_captures_temporary_reference_focus(self):
        defocus_reference_handler = MagicMock()
        self.autofocus_controller.parent_controller.event_listeners[
            "defocus_reference"
        ] = defocus_reference_handler
        payload = {
            "channel": "channel_1",
            "focus_position": 100.0,
            "calibration_action": "capture_reference",
        }

        self.autofocus_controller.handle_autofocus_complete(payload)

        assert self.autofocus_controller.defocus_calibration_reference == {
            "channel": "channel_1",
            "focus_position": 100.0,
        }
        defocus_reference_handler.assert_called_with(
            {"channel": "channel_1", "focus_position": 100.0}
        )

    def test_handle_autofocus_complete_populates_target_defocus_from_reference(self):
        channel_defocus_handler = MagicMock()
        defocus_reference_handler = MagicMock()
        self.autofocus_controller.parent_controller.event_listeners[
            "channel_defocus"
        ] = channel_defocus_handler
        self.autofocus_controller.parent_controller.event_listeners[
            "defocus_reference"
        ] = defocus_reference_handler
        self.autofocus_controller.defocus_calibration_reference = {
            "channel": "channel_1",
            "focus_position": 100.0,
        }
        channels = self.autofocus_controller.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]["channels"]
        channels["channel_2"]["defocus"] = 0.0

        self.autofocus_controller.handle_autofocus_complete(
            {
                "channel": "channel_2",
                "focus_position": 102.25,
                "calibration_action": "populate_defocus",
            }
        )

        assert channels["channel_2"]["defocus"] == pytest.approx(2.25)
        channel_defocus_handler.assert_called_with(("channel_2", 2.25))
        defocus_reference_handler.assert_called_with(
            {"channel": "channel_1", "focus_position": 100.0}
        )

    def test_handle_regular_autofocus_complete_restores_defocus_reference(self):
        defocus_reference_handler = MagicMock()
        self.autofocus_controller.parent_controller.event_listeners[
            "defocus_reference"
        ] = defocus_reference_handler
        self.autofocus_controller.defocus_calibration_reference = {
            "channel": "channel_1",
            "focus_position": 100.0,
        }

        self.autofocus_controller.handle_autofocus_complete(
            {
                "channel": "channel_2",
                "focus_position": 102.25,
                "calibration_action": None,
            }
        )

        defocus_reference_handler.assert_called_with(
            {"channel": "channel_1", "focus_position": 100.0}
        )

    def test_handle_autofocus_complete_does_not_populate_without_reference(self):
        channels = self.autofocus_controller.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]["channels"]
        channels["channel_2"]["defocus"] = 0.0

        with patch(
            "navigate.controller.sub_controllers.autofocus.messagebox.showwarning"
        ):
            self.autofocus_controller.handle_autofocus_complete(
                {
                    "channel": "channel_2",
                    "focus_position": 102.25,
                    "calibration_action": "populate_defocus",
                }
            )

        assert channels["channel_2"]["defocus"] == 0.0

        self.autofocus_controller.parent_controller.clear()

    def test_display_plot(self):
        """Tests that the display plot function works correctly

        Todo: Retrieve data from axessubplot instance and
        check that it is correct

        Raises
        ------
        AssertionError
            If the display plot function does not work correctly
        """
        # Make this robust by sending data and then
        # checking each plot is plotting correct data low priority

        x_data = np.linspace(start=69750.0, stop=70250.0, num=101)
        y_data = np.random.rand(101)
        data = [x_data, y_data]
        self.autofocus_controller.display_plot([data, False, True])
        pass
