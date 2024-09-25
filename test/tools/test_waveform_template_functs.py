# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard library imports
import unittest

# Third-party imports

# Local application imports
from navigate.tools.waveform_template_funcs import get_waveform_template_parameters


class TestGetWaveformTemplateParameters(unittest.TestCase):
    def setUp(self):
        self.waveform_template_name = "template1"
        self.waveform_template_dict = {
            "template1": {"repeat": 3, "expand": 2},
            "template2": {"repeat": "repeat_param", "expand": "expand_param"},
        }
        self.microscope_state_dict = {"repeat_param": 4, "expand_param": 5}

    def test_get_waveform_template_parameters(self):
        repeat_num, expand_num = get_waveform_template_parameters(
            self.waveform_template_name,
            self.waveform_template_dict,
            self.microscope_state_dict,
        )

        self.assertEqual(repeat_num, 3)
        self.assertEqual(expand_num, 2)

    def test_get_waveform_template_parameters_with_microscope_state(self):
        self.waveform_template_name = "template2"
        repeat_num, expand_num = get_waveform_template_parameters(
            self.waveform_template_name,
            self.waveform_template_dict,
            self.microscope_state_dict,
        )

        self.assertEqual(repeat_num, 4)
        self.assertEqual(expand_num, 5)

    def test_get_waveform_template_parameters_with_missing_template(self):
        self.waveform_template_name = "template3"
        repeat_num, expand_num = get_waveform_template_parameters(
            self.waveform_template_name,
            self.waveform_template_dict,
            self.microscope_state_dict,
        )

        self.assertEqual(repeat_num, 1)
        self.assertEqual(expand_num, 1)


class TestGetWaveformTemplateParametersExceptions(unittest.TestCase):
    def test_key_error_waveform_template_name(self):
        waveform_template_dict = {"template1": {"repeat": 2, "expand": 3}}
        microscope_state_dict = {}
        result = get_waveform_template_parameters(
            "nonexistent_template", waveform_template_dict, microscope_state_dict
        )
        self.assertEqual(
            result,
            (1, 1),
            "Default values should be returned when waveform template "
            "name is not found",
        )

    def test_key_error_repeat_key(self):
        waveform_template_dict = {"template1": {"expand": 3}}
        microscope_state_dict = {}
        result = get_waveform_template_parameters(
            "template1", waveform_template_dict, microscope_state_dict
        )
        self.assertEqual(
            result,
            (1, 3),
            "Default value for repeat_num should be returned "
            "when repeat key is not found",
        )

    def test_key_error_expand_key(self):
        waveform_template_dict = {"template1": {"repeat": 2}}
        microscope_state_dict = {}
        result = get_waveform_template_parameters(
            "template1", waveform_template_dict, microscope_state_dict
        )
        self.assertEqual(
            result,
            (2, 1),
            "Default value for expand_num should be returned"
            " when expand key is not found",
        )


if __name__ == "__main__":
    unittest.main()
