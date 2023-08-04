# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Imports

# Third Party Imports
import pytest

# Local Imports
from aslm.controller.sub_controllers.camera_setting_controller import (
    CameraSettingController,
)


class TestCameraSettingController:
    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        c = dummy_controller
        v = dummy_controller.view
        self.camera_settings = CameraSettingController(
            v.settings.camera_settings_tab, c
        )

    def test_init(self):

        assert isinstance(self.camera_settings, CameraSettingController)

        # Setup, going to check what the default values widgets are set too
        microscope_name = self.camera_settings.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]["microscope_name"]
        camera_config_dict = self.camera_settings.parent_controller.configuration[
            "configuration"
        ]["microscopes"][microscope_name]["camera"]

        # Default Values
        assert (
            self.camera_settings.default_pixel_size
            == camera_config_dict["pixel_size_in_microns"]
        )
        assert self.camera_settings.default_height == camera_config_dict["y_pixels"]
        assert self.camera_settings.default_width == camera_config_dict["x_pixels"]
        assert (
            self.camera_settings.trigger_source == camera_config_dict["trigger_source"]
        )
        assert (
            self.camera_settings.trigger_active == camera_config_dict["trigger_active"]
        )
        assert self.camera_settings.readout_speed == camera_config_dict["readout_speed"]

        # Camera Mode
        assert list(self.camera_settings.mode_widgets["Sensor"].widget["values"]) == [
            "Normal",
            "Light-Sheet",
        ]
        assert (
            str(self.camera_settings.mode_widgets["Sensor"].widget["state"])
            == "readonly"
        )

        # Readout Mode
        assert list(self.camera_settings.mode_widgets["Readout"].widget["values"]) == [
            " ",
            "Top-to-Bottom",
            "Bottom-to-Top",
        ]
        assert (
            str(self.camera_settings.mode_widgets["Readout"].widget["state"])
            == "disabled"
        )

        # Pixels
        assert (
            str(self.camera_settings.mode_widgets["Pixels"].widget["state"])
            == "disabled"
        )
        assert self.camera_settings.mode_widgets["Pixels"].widget.get() == ""
        assert self.camera_settings.mode_widgets["Pixels"].widget.cget("from") == 1
        assert (
            self.camera_settings.mode_widgets["Pixels"].widget.cget("to")
            == self.camera_settings.default_height / 2
        )
        assert self.camera_settings.mode_widgets["Pixels"].widget.cget("increment") == 1

        # Framerate
        assert (
            self.camera_settings.framerate_widgets["exposure_time"].widget.min
            == camera_config_dict["exposure_time_range"]["min"]
        )
        assert (
            self.camera_settings.framerate_widgets["exposure_time"].widget.max
            == camera_config_dict["exposure_time_range"]["max"]
        )
        assert (
            str(self.camera_settings.framerate_widgets["exposure_time"].widget["state"])
            == "disabled"
        )
        assert (
            str(self.camera_settings.framerate_widgets["readout_time"].widget["state"])
            == "disabled"
        )
        assert (
            str(self.camera_settings.framerate_widgets["max_framerate"].widget["state"])
            == "disabled"
        )

        # Set range value
        assert (
            self.camera_settings.roi_widgets["Width"].widget.cget("to")
            == self.camera_settings.default_width
        )
        assert self.camera_settings.roi_widgets["Width"].widget.cget("from") == 2
        assert self.camera_settings.roi_widgets["Width"].widget.cget("increment") == 2
        assert (
            self.camera_settings.roi_widgets["Height"].widget.cget("to")
            == self.camera_settings.default_height
        )
        assert self.camera_settings.roi_widgets["Height"].widget.cget("from") == 2
        assert self.camera_settings.roi_widgets["Height"].widget.cget("increment") == 2

        # Set binning options
        assert list(self.camera_settings.roi_widgets["Binning"].widget["values"]) == [
            "{}x{}".format(i, i) for i in [1, 2, 4]
        ]
        assert (
            str(self.camera_settings.roi_widgets["Binning"].widget["state"])
            == "readonly"
        )

        # Center position
        assert (
            self.camera_settings.roi_widgets["Center_X"].get()
            == self.camera_settings.default_width / 2
        )
        assert (
            self.camera_settings.roi_widgets["Center_Y"].get()
            == self.camera_settings.default_height / 2
        )
        assert (
            str(self.camera_settings.roi_widgets["Center_X"].widget["state"])
            == "disabled"
        )
        assert (
            str(self.camera_settings.roi_widgets["Center_Y"].widget["state"])
            == "disabled"
        )

        # FOV
        assert (
            str(self.camera_settings.roi_widgets["FOV_X"].widget["state"]) == "disabled"
        )
        assert (
            str(self.camera_settings.roi_widgets["FOV_Y"].widget["state"]) == "disabled"
        )

    def test_attr(self):

        attrs = [
            "in_initialization",
            "resolution_value",
            "mode",
            "solvent",
            "mode_widgets",
            "framerate_widgets",
            "roi_widgets",
            "roi_btns",
            "default_pixel_size",
            "default_width",
            "default_height",
            "trigger_source",
            "trigger_active",
            "readout_speed",
            "pixel_event_id",
        ]

        for attr in attrs:
            assert hasattr(self.camera_settings, attr)

    def test_populate_experiment_values(self):

        # Populate widgets with values from experiment file and check
        self.camera_settings.populate_experiment_values()
        camera_setting_dict = self.camera_settings.parent_controller.configuration[
            "experiment"
        ]["CameraParameters"]

        # Checking values altered are correct
        assert dict(self.camera_settings.camera_setting_dict) == dict(
            self.camera_settings.parent_controller.configuration["experiment"][
                "CameraParameters"
            ]
        )
        assert (
            str(self.camera_settings.mode_widgets["Sensor"].get())
            == camera_setting_dict["sensor_mode"]
        )
        if camera_setting_dict["sensor_mode"] == "Normal":
            assert str(self.camera_settings.mode_widgets["Readout"].get()) == ""
            assert str(self.camera_settings.mode_widgets["Pixels"].get()) == ""
        elif camera_setting_dict["sensor_mode"] == "Light-Sheet":
            assert (
                str(self.camera_settings.mode_widgets["Readout"].get())
                == self.camera_settings.camera_setting_dict["readout_direction"]
            )
            assert (
                str(self.camera_settings.mode_widgets["Pixels"].get())
                == self.camera_settings.camera_setting_dict["number_of_pixels"]
            )

        # ROI
        assert (
            self.camera_settings.roi_widgets["Width"].get()
            == camera_setting_dict["x_pixels"]
        )
        assert (
            self.camera_settings.roi_widgets["Height"].get()
            == camera_setting_dict["y_pixels"]
        )

        # Binning
        assert (
            str(self.camera_settings.roi_widgets["Binning"].get())
            == camera_setting_dict["binning"]
        )

        # Exposure Time
        channels = self.camera_settings.microscope_state_dict["channels"]
        exposure_time = channels[list(channels.keys())[0]]["camera_exposure_time"]
        assert (
            self.camera_settings.framerate_widgets["exposure_time"].get()
            == exposure_time
        )
        assert (
            self.camera_settings.framerate_widgets["frames_to_average"].get()
            == camera_setting_dict["frames_to_average"]
        )
        assert self.camera_settings.in_initialization is False

    @pytest.mark.parametrize("mode", ["Normal", "Light-Sheet"])
    def test_update_experiment_values(self, mode):

        # Setup basic default experiment
        self.camera_settings.camera_setting_dict = (
            self.camera_settings.parent_controller.configuration["experiment"][
                "CameraParameters"
            ]
        )

        # Setting up new values in widgets
        self.camera_settings.mode_widgets["Sensor"].set(mode)
        self.camera_settings.roi_widgets["Binning"].set("4x4")
        if mode == "Light-Sheet":
            self.camera_settings.mode_widgets["Readout"].set("Bottom-to-Top")
            self.camera_settings.mode_widgets["Pixels"].set(15)
            self.camera_settings.roi_widgets["Binning"].set("1x1")
        self.camera_settings.roi_widgets["Width"].set(1600)
        self.camera_settings.roi_widgets["Height"].set(1600)
        self.camera_settings.framerate_widgets["frames_to_average"].set(5)

        # Update experiment dict and assert
        self.camera_settings.update_experiment_values()
        assert self.camera_settings.camera_setting_dict["sensor_mode"] == mode
        if mode == "Light-Sheet":
            assert (
                self.camera_settings.camera_setting_dict["readout_direction"]
                == "Bottom-to-Top"
            )
            assert (
                int(self.camera_settings.camera_setting_dict["number_of_pixels"]) == 15
            )
        if mode == "Light-Sheet":
            assert self.camera_settings.camera_setting_dict["binning"] == "1x1"
            assert self.camera_settings.camera_setting_dict["img_x_pixels"] == 1600
            assert self.camera_settings.camera_setting_dict["img_y_pixels"] == 1600
        else:
            assert self.camera_settings.camera_setting_dict["binning"] == "4x4"
            assert self.camera_settings.camera_setting_dict["img_x_pixels"] == 400
            assert self.camera_settings.camera_setting_dict["img_y_pixels"] == 400
        assert self.camera_settings.camera_setting_dict["x_pixels"] == 1600
        assert self.camera_settings.camera_setting_dict["y_pixels"] == 1600
        assert (
            self.camera_settings.camera_setting_dict["pixel_size"]
            == self.camera_settings.default_pixel_size
        )
        assert self.camera_settings.camera_setting_dict["frames_to_average"] == 5

    @pytest.mark.parametrize("mode", ["Normal", "Light-Sheet"])
    def test_update_sensor_mode(self, mode):
        self.camera_settings.populate_experiment_values()
        camera_setting_dict = self.camera_settings.parent_controller.configuration[
            "experiment"
        ]["CameraParameters"]

        # Set mode
        self.camera_settings.mode_widgets["Sensor"].widget.set(mode)
        self.camera_settings.mode_widgets["Sensor"].widget.event_generate(
            "<<ComboboxSelected>>"
        )

        # Call update
        # self.camera_settings.update_sensor_mode()

        # Check values
        if mode == "Normal":
            assert str(self.camera_settings.mode_widgets["Readout"].get()) == " "
            assert (
                str(self.camera_settings.mode_widgets["Readout"].widget["state"])
                == "disabled"
            )
            assert (
                str(self.camera_settings.mode_widgets["Pixels"].widget["state"])
                == "disabled"
            )
            assert str(self.camera_settings.mode_widgets["Pixels"].widget.get()) == ""

        if mode == "Light-Sheet":
            assert (
                str(self.camera_settings.mode_widgets["Readout"].get())
                == camera_setting_dict["readout_direction"]
            )
            assert (
                str(self.camera_settings.mode_widgets["Readout"].widget["state"])
                == "readonly"
            )
            assert (
                str(self.camera_settings.mode_widgets["Pixels"].widget["state"])
                == "normal"
            )
            assert int(self.camera_settings.mode_widgets["Pixels"].widget.get()) == int(
                self.camera_settings.camera_setting_dict["number_of_pixels"]
            )

    def test_update_exposure_time(self):

        # Call funciton
        self.camera_settings.update_exposure_time(35)

        # Check
        assert self.camera_settings.framerate_widgets["exposure_time"].get() == 35

    @pytest.mark.parametrize("name", ["All", "1600", "1024", "512"])
    def test_update_roi(self, name):

        # Call button to check if handler setup correctly
        self.camera_settings.roi_btns[name].invoke()

        # Check
        if name == "All":
            name = "2048"
        assert str(self.camera_settings.roi_widgets["Width"].get()) == name
        assert str(self.camera_settings.roi_widgets["Height"].get()) == name

    def test_update_fov(self):

        # Invoke commands

        # Change invoke
        self.camera_settings.in_initialization = False
        self.camera_settings.roi_widgets["Width"].widget.set(2048)
        self.camera_settings.roi_widgets["Height"].widget.set(2048)
        xFov = int(self.camera_settings.roi_widgets["FOV_X"].get())
        yFov = int(self.camera_settings.roi_widgets["FOV_Y"].get())
        self.camera_settings.roi_widgets["Width"].widget.set(1600)
        self.camera_settings.roi_widgets["Height"].widget.set(1600)

        # Check
        assert xFov != int(self.camera_settings.roi_widgets["FOV_X"].get())
        assert yFov != int(self.camera_settings.roi_widgets["FOV_Y"].get())

        # Reset
        self.camera_settings.roi_widgets["Width"].widget.set(2048)
        self.camera_settings.roi_widgets["Height"].widget.set(2048)
        assert int(self.camera_settings.roi_widgets["FOV_X"].get()) == 13066
        assert int(self.camera_settings.roi_widgets["FOV_Y"].get()) == 13066

    @pytest.mark.parametrize("mode", ["live", "z-stack", "stop", "single"])
    @pytest.mark.parametrize("readout", ["Normal", "Light-Sheet"])
    def test_set_mode(self, mode, readout):

        # Populate widgets with values from experiment file
        self.camera_settings.populate_experiment_values()

        # Set mode
        self.camera_settings.mode_widgets["Sensor"].widget.set(readout)
        self.camera_settings.update_sensor_mode()
        self.camera_settings.set_mode(mode)

        # Check
        assert self.camera_settings.mode == mode
        if mode != "stop":
            state = "disabled"
        else:
            state = "normal"
        if mode != "stop":
            state_readonly = "disabled"
        else:
            state_readonly = "readonly"

        assert (
            str(self.camera_settings.mode_widgets["Sensor"].widget["state"])
            == state_readonly
        )
        if str(self.camera_settings.mode_widgets["Sensor"].get()) == "Light-Sheet":
            assert (
                str(self.camera_settings.mode_widgets["Readout"].widget["state"])
                == state_readonly
            )
            if mode == "live":
                assert (
                    str(self.camera_settings.mode_widgets["Pixels"].widget["state"])
                    == "normal"
                )
            else:
                assert (
                    str(self.camera_settings.mode_widgets["Pixels"].widget["state"])
                    == state
                )
        else:
            assert (
                str(self.camera_settings.mode_widgets["Readout"].widget["state"])
                == "disabled"
            )
            assert (
                str(self.camera_settings.mode_widgets["Pixels"].widget["state"])
                == "disabled"
            )
        assert (
            str(
                self.camera_settings.framerate_widgets["frames_to_average"].widget[
                    "state"
                ]
            )
            == state
        )
        assert str(self.camera_settings.roi_widgets["Width"].widget["state"]) == state
        assert str(self.camera_settings.roi_widgets["Height"].widget["state"]) == state
        assert (
            str(self.camera_settings.roi_widgets["Binning"].widget["state"])
            == state_readonly
        )
        for btn_name in self.camera_settings.roi_btns:
            assert str(self.camera_settings.roi_btns[btn_name]["state"]) == state

    @pytest.mark.parametrize("zoom", ["0.63x", "1x", "2x", "3x", "4x", "5x", "6x"])
    def test_calculate_physical_dimensions(self, zoom):
        self.camera_settings.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["zoom"] = zoom

        # Calling
        self.camera_settings.calculate_physical_dimensions()

        pixel_size = self.camera_settings.default_pixel_size
        x_pixel = float(self.camera_settings.roi_widgets["Width"].get())
        y_pixel = float(self.camera_settings.roi_widgets["Height"].get())

        microscope_state_dict = self.camera_settings.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]
        zoom = microscope_state_dict["zoom"]
        microscope_name = microscope_state_dict["microscope_name"]
        pixel_size = self.camera_settings.parent_controller.configuration[
            "configuration"
        ]["microscopes"][microscope_name]["zoom"]["pixel_size"][zoom]

        dim_x = x_pixel * pixel_size
        dim_y = y_pixel * pixel_size

        assert float(self.camera_settings.roi_widgets["FOV_X"].get()) == float(
            int(dim_x)
        )
        assert float(self.camera_settings.roi_widgets["FOV_Y"].get()) == float(
            int(dim_y)
        )

        # Reset to zoom of 1
        self.camera_settings.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["zoom"] = "1x"
        assert (
            self.camera_settings.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["zoom"]
            == "1x"
        )

    def test_calculate_readout_time(self):
        """
        TODO need more info about camera before testing
        """
        pass

    @pytest.mark.parametrize(
        "mode", ["single", "live", "customized", "projection", "z-stack", "stop"]
    )
    def test_update_number_of_pixels(self, mode):
        import random

        self.camera_settings.populate_experiment_values()

        self.camera_settings.mode = mode

        self.camera_settings.mode_widgets["Pixels"].set("")
        assert self.camera_settings.camera_setting_dict["number_of_pixels"] != ""

        n_pixels = random.randint(1, 100)
        self.camera_settings.mode_widgets["Pixels"].set(n_pixels)

        # Check
        assert self.camera_settings.camera_setting_dict["number_of_pixels"] == int(
            n_pixels
        )
        if mode != "live" and mode != "stop":
            assert (
                self.camera_settings.camera_setting_dict["number_of_pixels"] == n_pixels
            )

    @pytest.mark.parametrize(
        "x_pixels, y_pixels", [(512, 512), (4096, 4096), (2304, 1024), (1024, 2048)]
    )
    def test_update_camera_device_related_setting(self, x_pixels, y_pixels):
        self.camera_settings.populate_experiment_values()

        microscope_name = self.camera_settings.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]["microscope_name"]
        camera_config = self.camera_settings.parent_controller.configuration[
            "configuration"
        ]["microscopes"][microscope_name]["camera"]
        default_x_pixels = camera_config["x_pixels"]
        default_y_pixels = camera_config["y_pixels"]

        camera_config["x_pixels"] = x_pixels
        camera_config["y_pixels"] = y_pixels
        self.camera_settings.update_camera_device_related_setting()

        assert self.camera_settings.roi_widgets["Width"].get() == min(
            self.camera_settings.camera_setting_dict["x_pixels"], x_pixels
        )
        assert self.camera_settings.roi_widgets["Height"].get() == min(
            self.camera_settings.camera_setting_dict["y_pixels"], y_pixels
        )
        assert self.camera_settings.roi_widgets["Width"].widget["to"] == x_pixels
        assert self.camera_settings.roi_widgets["Height"].widget["to"] == y_pixels

        camera_config["x_pixels"] = default_x_pixels
        camera_config["y_pixels"] = default_y_pixels
