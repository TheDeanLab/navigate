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
import datetime

# Third Party Imports

# Local Imports


class TextExperimentFile(unittest.TestCase):
    """Test the experiment configuration file."""

    def setUp(self):
        current_path = os.path.abspath(os.path.dirname(__file__))
        root_path = os.path.dirname(os.path.dirname(current_path))
        yaml_path = os.path.join(root_path, "src", "navigate", "config", "experiment.yml")

        with open(yaml_path) as file:
            self.data = yaml.safe_load(file)

    def tearDown(self):
        pass

    def parse_entries(self, section, expected_values):
        """Parse the entries in the configuration file.

        Parameters
        ----------
        section : str
            The section of the configuration file to parse
        expected_values : dict
            A dictionary of expected values for the section


        Raises
        ------
        AssertionError
            If the key is not in the section or if the value is not the expected type
        """
        keys = self.data[section].keys()
        for key in keys:
            self.assertIn(key, expected_values)
            assert isinstance(
                self.data[section][key], expected_values[key]
            ), f"{key} is not of type {expected_values[key]}"

    def test_user(self):
        expected_values = {"name": str}

        self.parse_entries(section="User", expected_values=expected_values)

    def test_saving(self):
        expected_values = {
            "root_directory": str,
            "save_directory": str,
            "user": str,
            "tissue": str,
            "celltype": str,
            "label": str,
            "file_type": str,
            "date": datetime.date,
            "solvent": str,
        }

        self.parse_entries(section="Saving", expected_values=expected_values)

    def test_camera_parameters(self):
        expected_values = {
            "x_pixels": int,
            "y_pixels": int,
            "sensor_mode": str,
            "readout_direction": str,
            "number_of_pixels": int,
            "binning": str,
            "pixel_size": float,
            "frames_to_average": float,
            "databuffer_size": int,
        }

        self.parse_entries(section="CameraParameters", expected_values=expected_values)

    # TODO: This test case could be removed after PR#452 is merged into Develop.
    def test_autofocus_parameters(self):
        expected_values = {
            "coarse_range": int,
            "coarse_step_size": int,
            "coarse_selected": int,
            "fine_range": int,
            "fine_step_size": int,
            "fine_selected": bool,
            "robust_fit": bool,
        }

        self.parse_entries(
            section="AutoFocusParameters", expected_values=expected_values
        )

    def test_stage_parameters(self):
        expected_values = {
            "xy_step": float,
            "z_step": float,
            "theta_step": float,
            "f_step": float,
            "x": float,
            "y": float,
            "z": float,
            "theta": float,
            "f": float,
            "limits": bool,
        }

        self.parse_entries(section="StageParameters", expected_values=expected_values)

    def test_microscope_state(self):
        expected_values = {
            "microscope_name": str,
            "image_mode": str,
            "zoom": str,
            "stack_cycling_mode": str,
            "start_position": float,
            "end_position": float,
            "step_size": float,
            "number_z_steps": float,
            "timepoints": int,
            "stack_pause": float,
            "is_save": bool,
            "stack_acq_time": float,
            "timepoint_interval": int,
            "experiment_duration": float,
            "is_multiposition": bool,
            "multiposition_count": int,
            "selected_channels": int,
            "channels": dict,
            "stack_z_origin": float,
            "stack_focus_origin": float,
            "start_focus": float,
            "end_focus": float,
            "abs_z_start": float,
            "abs_z_end": float,
            "waveform_template": str,
        }

        self.parse_entries(section="MicroscopeState", expected_values=expected_values)

        # Check that the channels dictionary has the correct keys
        channel_keys = self.data["MicroscopeState"]["channels"].keys()
        for key in channel_keys:
            # Number of channels can vary depending upon the experiment.
            assert "channel_" in key
            expected_values = {
                "is_selected": bool,
                "laser": str,
                "laser_index": int,
                "filter": str,
                "filter_position": int,
                "camera_exposure_time": float,
                "laser_power": str,
                "interval_time": str,
                "defocus": float,
            }

            key_keys = self.data["MicroscopeState"]["channels"][key].keys()
            for key_key in key_keys:
                self.assertIn(key_key, expected_values)
                assert isinstance(
                    self.data["MicroscopeState"]["channels"][key][key_key],
                    expected_values[key_key],
                ), f"{key_key} is not of type {expected_values[key_key]}"

    def test_multiposition(self):
        expected_values = [float, float, float, float, float]
        positions = self.data["MultiPositions"]
        print("*** positions:", positions)
        for position in positions:
            for i in range(len(expected_values)):
                assert isinstance(
                    position[i], expected_values[i]
                ), f"{i} is not of type {expected_values[i]}"
