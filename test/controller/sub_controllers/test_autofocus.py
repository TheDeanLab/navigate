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

# Third party imports
import pytest
import numpy as np

# Local application imports
from navigate.controller.sub_controllers import AutofocusPopupController
from navigate.view.popups.autofocus_setting_popup import AutofocusPopup


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
        self.autofocus_controller.widgets["calibration_action"].set(
            "Capture Reference"
        )

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
            f"CH{channel_key.removeprefix('channel_')}"
            for channel_key in channel_keys
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
