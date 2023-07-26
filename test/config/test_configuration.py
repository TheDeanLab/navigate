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
import unittest
import yaml
import os

# Third Party Imports

# Local Imports


class TestConfiguration(unittest.TestCase):
    def setUp(self):
        current_path = os.path.abspath(os.path.dirname(__file__))
        root_path = os.path.dirname(os.path.dirname(current_path))
        yaml_path = os.path.join(
            root_path, "src", "aslm", "config", "configuration.yaml"
        )

        with open(yaml_path) as file:
            self.data = yaml.safe_load(file)

    def tearDown(self):
        pass

    def test_hardware_section(self):
        expected_hardware = ["daq", "camera", "filter_wheel", "stage", "zoom"]

        hardware_types = self.data["hardware"].keys()
        for hardware_type in hardware_types:
            self.assertIn(hardware_type, expected_hardware)
            if isinstance(self.data["hardware"][hardware_type], dict):
                hardware_keys = self.data["hardware"][hardware_type].keys()
                for key in hardware_keys:
                    self.assertIn("type", self.data["hardware"][hardware_type])
            elif isinstance(self.data["hardware"][hardware_type], list):
                for i in range(len(self.data["hardware"][hardware_type])):
                    self.assertIn("type", self.data["hardware"][hardware_type][i])

    def test_gui_section(self):
        expected_keys = ["channels", "stack_acquisition", "timepoint"]
        expected_channel_keys = [
            "count",
            "laser_power",
            "exposure_time",
            "interval_time",
        ]
        expected_stack_keys = ["step_size", "start_pos", "end_pos"]
        min_max_step_keys = ["min", "max", "step"]

        gui_keys = self.data["gui"].keys()
        for key in gui_keys:
            self.assertIn(key, expected_keys)

            # Channels Entry
            if key == "channels":
                channel_keys = self.data["gui"][key].keys()
                for channel_key in channel_keys:
                    self.assertIn(channel_key, expected_channel_keys)
                    if channel_key != "count":
                        channel_key_keys = self.data["gui"][key][channel_key].keys()
                        for channel_key_key in channel_key_keys:
                            self.assertIn(channel_key_key, min_max_step_keys)

            # Stack Acquisition Entry
            elif key == "stack_acquisition":
                stack_keys = self.data["gui"][key].keys()
                for stack_key in stack_keys:
                    self.assertIn(stack_key, expected_stack_keys)
                    stack_key_keys = self.data["gui"][key][stack_key].keys()
                    for stack_key_key in stack_key_keys:
                        self.assertIn(stack_key_key, min_max_step_keys)

            # Timepoint Entry
            elif key == "timepoint":
                timepoint_keys = self.data["gui"][key].keys()
                for timepoint_key in timepoint_keys:
                    timepoint_key_keys = self.data["gui"][key][timepoint_key].keys()
                    for timepoint_key_key in timepoint_key_keys:
                        self.assertIn(timepoint_key_key, min_max_step_keys)

            else:
                raise ValueError("Unexpected key in gui section")

    def test_microscope_section(self):
        expected_hardware = [
            "daq",
            "camera",
            "remote_focus_device",
            "galvo",
            "shutter",
            "lasers",
            "filter_wheel",
            "stage",
            "zoom",
        ]

        microscopes = self.data["microscopes"].keys()
        for microscope in microscopes:
            hardware = self.data["microscopes"][microscope].keys()
            for hardware_type in hardware:
                self.assertIn(hardware_type, expected_hardware)

                if hardware_type == "daq":
                    self.daq_section(microscope=microscope, hardware_type=hardware_type)

                elif hardware_type == "camera":
                    self.camera_section(
                        microscope=microscope, hardware_type=hardware_type
                    )

                elif hardware_type == "remote_focus_device":
                    self.remote_focus_section(
                        microscope=microscope, hardware_type=hardware_type
                    )

                elif hardware_type == "galvo":
                    self.galvo_section(
                        microscope=microscope, hardware_type=hardware_type
                    )

                elif hardware_type == "filter_wheel":
                    self.filter_wheel_section(
                        microscope=microscope, hardware_type=hardware_type
                    )
                elif hardware_type == "stage":
                    self.stage_section(
                        microscope=microscope, hardware_type=hardware_type
                    )

                elif hardware_type == "zoom":
                    self.zoom_section(
                        microscope=microscope, hardware_type=hardware_type
                    )

                elif hardware_type == "shutter":
                    self.shutter_section(
                        microscope=microscope, hardware_type=hardware_type
                    )

                elif hardware_type == "lasers":
                    self.laser_section(
                        microscope=microscope, hardware_type=hardware_type
                    )

                else:
                    raise ValueError("Unexpected hardware type")

    def daq_section(self, microscope, hardware_type):
        expected_daq_keys = [
            "hardware",
            "sample_rate",
            "sweep_time",
            "master_trigger_out_line",
            "camera_trigger_out_line",
            "trigger_source",
            "laser_port_switcher",
            "laser_switch_state",
        ]
        type_keys = ["name", "type"]

        daq_keys = self.data["microscopes"][microscope][hardware_type].keys()
        for key in daq_keys:
            if key == "hardware":
                for type_key in type_keys:
                    self.assertIn(
                        type_key,
                        self.data["microscopes"][microscope][hardware_type][key],
                    )
            else:
                self.assertIn(key, expected_daq_keys)

    def camera_section(self, microscope, hardware_type):
        expected_keys = [
            "hardware",
            "x_pixels",
            "y_pixels",
            "pixel_size_in_microns",
            "subsampling",
            "sensor_mode",
            "readout_direction",
            "lightsheet_rolling_shutter_width",
            "defect_correct_mode",
            "binning",
            "readout_speed",
            "trigger_active",
            "trigger_mode",
            "trigger_polarity",
            "trigger_source",
            "exposure_time",
            "delay_percent",
            "pulse_percent",
            "line_interval",
            "display_acquisition_subsampling",
            "average_frame_rate",
            "frames_to_average",
            "exposure_time_range",
        ]
        type_keys = ["name", "type"]

        camera_keys = self.data["microscopes"][microscope][hardware_type].keys()
        for key in camera_keys:
            if key == "hardware":
                for type_key in type_keys:
                    self.assertIn(
                        type_key,
                        self.data["microscopes"][microscope][hardware_type][key],
                    )
            else:
                self.assertIn(key, expected_keys)

    def remote_focus_section(self, microscope, hardware_type):
        expected_keys = [
            "hardware",
            "delay_percent",
            "ramp_rising_percent",
            "ramp_falling_percent",
            "amplitude",
            "offset",
            "smoothing",
        ]
        type_keys = ["name", "type", "channel", "min", "max"]
        remote_focus_keys = self.data["microscopes"][microscope][hardware_type].keys()
        for key in remote_focus_keys:
            if key == "hardware":
                for type_key in type_keys:
                    self.assertIn(
                        type_key,
                        self.data["microscopes"][microscope][hardware_type][key],
                    )
            else:
                self.assertIn(key, expected_keys)

    def galvo_section(self, microscope, hardware_type):
        expected_keys = [
            "hardware",
            "waveform",
            "frequency",
            "amplitude",
            "offset",
            "duty_cycle",
            "phase",
        ]
        type_keys = ["name", "type", "channel", "min", "max"]

        if isinstance(self.data["microscopes"][microscope][hardware_type], list):
            for i in range(len(self.data["microscopes"][microscope][hardware_type])):
                galvo_keys = self.data["microscopes"][microscope][hardware_type][
                    i
                ].keys()
                for key in galvo_keys:
                    if key == "hardware":
                        for type_key in type_keys:
                            self.assertIn(
                                type_key,
                                self.data["microscopes"][microscope][hardware_type][i][
                                    key
                                ],
                            )
                    else:
                        self.assertIn(key, expected_keys)
        else:
            raise ValueError("Galvo section is not a list")

    def filter_wheel_section(self, microscope, hardware_type):
        expected_keys = [
            "hardware",
            "filter_wheel_delay",
            "available_filters",
        ]
        type_keys = ["name", "type", "wheel_number"]

        keys = self.data["microscopes"][microscope][hardware_type].keys()
        for key in keys:
            if key == "hardware":
                for type_key in type_keys:
                    self.assertIn(
                        type_key,
                        self.data["microscopes"][microscope][hardware_type][key],
                    )
            elif key == "available_filters":
                assert isinstance(
                    self.data["microscopes"][microscope][hardware_type][key], dict
                )
            else:
                self.assertIn(key, expected_keys)

    def stage_section(self, microscope, hardware_type):
        expected_keys = [
            "hardware",
            "x_max",
            "x_min",
            "y_max",
            "y_min",
            "z_max",
            "z_min",
            "f_max",
            "f_min",
            "theta_max",
            "theta_min",
            "x_step",
            "y_step",
            "z_step",
            "theta_step",
            "f_step",
            "velocity",
            "x_offset",
            "y_offset",
            "z_offset",
            "theta_offset",
            "f_offset",
            "joystick_axes",
        ]
        type_keys = [
            "name",
            "type",
            "serial_number",
            "axes",
            "volts_per_micron",
            "axes_channels",
            "max",
            "min",
        ]

        for key in self.data["microscopes"][microscope][hardware_type].keys():
            if key == "hardware":
                if isinstance(
                    self.data["microscopes"][microscope][hardware_type][key], list
                ):
                    for i in range(
                        len(self.data["microscopes"][microscope][hardware_type][key])
                    ):
                        for type_key in type_keys:
                            self.assertIn(
                                type_key,
                                self.data["microscopes"][microscope][hardware_type][
                                    key
                                ][i],
                            )
                elif isinstance(
                    self.data["microscopes"][microscope][hardware_type][key], dict
                ):
                    for type_key in type_keys:
                        self.assertIn(
                            type_key,
                            self.data["microscopes"][microscope][hardware_type][key],
                        )
                else:
                    raise ValueError("Stage hardware is not a list or dict")
            else:
                self.assertIn(key, expected_keys)

    def zoom_section(self, microscope, hardware_type):
        expected_keys = ["hardware", "position", "pixel_size", "stage_positions"]
        type_keys = ["name", "type", "servo_id"]

        for key in self.data["microscopes"][microscope][hardware_type].keys():
            if key == "hardware":
                for type_key in type_keys:
                    self.assertIn(
                        type_key,
                        self.data["microscopes"][microscope][hardware_type][key],
                    )
            elif key == "position":
                assert isinstance(
                    self.data["microscopes"][microscope][hardware_type][key], dict
                )
            elif key == "pixel_size":
                assert isinstance(
                    self.data["microscopes"][microscope][hardware_type][key], dict
                )
            elif key == "stage_positions":
                assert isinstance(
                    self.data["microscopes"][microscope][hardware_type][key], dict
                )
            else:
                self.assertIn(key, expected_keys)

    def shutter_section(self, microscope, hardware_type):
        expected_keys = ["hardware", "shutter_min_do", "shutter_max_do"]
        type_keys = ["name", "type", "channel"]

        for key in self.data["microscopes"][microscope][hardware_type].keys():
            if key == "hardware":
                for type_key in type_keys:
                    self.assertIn(
                        type_key,
                        self.data["microscopes"][microscope][hardware_type][key],
                    )
            else:
                self.assertIn(key, expected_keys)

    def laser_section(self, microscope, hardware_type):
        expected_keys = [
            "wavelength",
            "onoff",
            "power",
            "type",
            "index",
            "delay_percent",
            "pulse_percent",
        ]

        hardware_keys = ["name", "type", "channel", "min", "max"]

        if isinstance(self.data["microscopes"][microscope][hardware_type], list):
            for i in range(len(self.data["microscopes"][microscope][hardware_type])):
                laser_keys = self.data["microscopes"][microscope][hardware_type][
                    i
                ].keys()
                for key in laser_keys:
                    if key == "onoff" or key == "power":
                        onoff_keys = self.data["microscopes"][microscope][
                            hardware_type
                        ][i][key]["hardware"].keys()
                        for onoff_key in onoff_keys:
                            self.assertIn(onoff_key, hardware_keys)
                    else:
                        self.assertIn(key, expected_keys)
        else:
            raise ValueError("Laser section is not a list")
