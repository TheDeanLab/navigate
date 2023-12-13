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


class TestWaveformConstants(unittest.TestCase):
    def test_yaml_structure(self):
        current_path = os.path.abspath(os.path.dirname(__file__))
        root_path = os.path.dirname(os.path.dirname(current_path))
        yaml_path = os.path.join(
            root_path, "src", "navigate", "config", "waveform_constants.yml"
        )

        # Load the YAML file
        with open(yaml_path) as file:
            data = yaml.safe_load(file)

        expected_keys = ["amplitude", "offset", "percent_smoothing", "percent_delay"]

        microscope_names = data["remote_focus_constants"].keys()
        for microscope_name in microscope_names:
            assert isinstance(microscope_name, str)

            magnifications = data["remote_focus_constants"][microscope_name].keys()
            for magnification in magnifications:
                assert isinstance(magnification, str)

                wavelengths = data["remote_focus_constants"][microscope_name][
                    magnification
                ].keys()
                for wavelength in wavelengths:
                    assert isinstance(wavelength, str)

                    for key in expected_keys:
                        assert (
                            key
                            in data["remote_focus_constants"][microscope_name][
                                magnification
                            ][wavelength].keys()
                        )

        expected_keys = ["amplitude", "offset", "frequency"]

        galvos = data["galvo_constants"].keys()
        for galvo in galvos:
            assert isinstance(galvo, str)

            for microscope_name in microscope_names:
                assert microscope_name in data["galvo_constants"][galvo].keys()

                magnifications = data["galvo_constants"][galvo][microscope_name].keys()
                for magnification in magnifications:
                    assert (
                        magnification
                        in data["galvo_constants"][galvo][microscope_name].keys()
                    )
                    for key in expected_keys:
                        assert (
                            key
                            in data["galvo_constants"][galvo][microscope_name][
                                magnification
                            ].keys()
                        )

        other_constants = data["other_constants"].keys()
        assert "remote_focus_settle_duration" in other_constants

if __name__ == "__main__":
    unittest.main()
