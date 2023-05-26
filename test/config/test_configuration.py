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

                # DAQ Section
                if hardware_type == "daq":
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

                    daq_keys = self.data["microscopes"][microscope][
                        hardware_type
                    ].keys()
                    for key in daq_keys:
                        if key == "hardware":
                            self.assertIn(
                                "name",
                                self.data["microscopes"][microscope][hardware_type][
                                    key
                                ],
                            )
                            self.assertIn(
                                "type",
                                self.data["microscopes"][microscope][hardware_type][
                                    key
                                ],
                            )
                        else:
                            self.assertIn(key, expected_daq_keys)

                # Camera Section
                elif hardware_type == "camera":
                    # TODO: Keeping short as we want to modify this section
                    expected_camera_keys = ["hardware", "x_pixels", "y_pixels"]
                    for key in expected_camera_keys:
                        if key == "hardware":
                            self.assertIn(
                                "type",
                                self.data["microscopes"][microscope][hardware_type][
                                    key
                                ],
                            )
                            self.assertIn(
                                "name",
                                self.data["microscopes"][microscope][hardware_type][
                                    key
                                ],
                            )
                            self.assertIn(
                                "serial_number",
                                self.data["microscopes"][microscope][hardware_type][
                                    key
                                ],
                            )
                        else:
                            self.assertIn(key, expected_camera_keys)
