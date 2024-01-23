# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

# Third party imports
import numpy as np

# Local imports
from navigate.model.features.autofocus import power_tent
from navigate.model.features.autofocus import Autofocus
from test.model.dummy import DummyModel


class TestPowerTentFunction(unittest.TestCase):
    def test_power_tent(self):
        # Test with known parameters and expected result
        x = 2.0
        x_offset = 1.0
        y_offset = 0.0
        amplitude = 2.0
        sigma = 0.5
        alpha = 2.0

        # Calculate the expected result manually
        expected_result = y_offset + amplitude * (
            1 - np.abs(sigma * (x - x_offset)) ** alpha
        )

        # Call the function and check if the result is close to the expected result
        result = power_tent(x, x_offset, y_offset, amplitude, sigma, alpha)
        self.assertAlmostEqual(result, expected_result, places=6)

    def test_power_tent_boundary_cases(self):
        # Test some boundary cases
        x_offset = 0.0
        y_offset = 0.0
        amplitude = 1.0
        sigma = 1.0
        alpha = 1.0

        # Test at x = x_offset, should be y_offset + amplitude
        result = power_tent(x_offset, x_offset, y_offset, amplitude, sigma, alpha)
        self.assertAlmostEqual(result, y_offset + amplitude, places=6)

        # Test at x = x_offset + 1, should be y_offset
        result = power_tent(x_offset + 1, x_offset, y_offset, amplitude, sigma, alpha)
        self.assertAlmostEqual(result, y_offset, places=6)


class TestAutofocusClass(unittest.TestCase):
    def setUp(self):
        # Initialize an instance of the Autofocus class for testing
        model = DummyModel()
        model.active_microscope_name = "Mesoscale"
        self.autofocus = Autofocus(model=model, device="stage", device_ref="f")

    def test_get_autofocus_frame_num(self):
        # Test the get_autofocus_frame_num method
        settings = {
            "coarse_selected": True,
            "coarse_range": 8.0,
            "coarse_step_size": 2.0,
            "fine_selected": True,
            "fine_range": 5.0,
            "fine_step_size": 1.0,
        }
        self.autofocus.model.configuration = {
            "experiment": {
                "AutoFocusParameters": {"Mesoscale": {"stage": {"f": settings}}}
            }
        }
        # Both Fine and Coarse Selected
        frames = self.autofocus.get_autofocus_frame_num()
        self.assertEqual(frames, 11)  # Expected number of frames

        # Only Coarse Selected
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["fine_selected"] = False
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["coarse_selected"] = True
        frames = self.autofocus.get_autofocus_frame_num()
        self.assertEqual(frames, 5)  # Expected number of frames

        # Only Fine Selected
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["fine_selected"] = True
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["coarse_selected"] = False
        frames = self.autofocus.get_autofocus_frame_num()
        self.assertEqual(frames, 6)  # Expected number of frames

    def test_get_steps(self):
        # Test the get_steps method
        steps, pos_offset = self.autofocus.get_steps(10.0, 2.0)
        self.assertEqual(steps, 6)  # Expected number of steps
        self.assertEqual(pos_offset, 8.0)  # Expected position offset


if __name__ == "__main__":
    unittest.main()
