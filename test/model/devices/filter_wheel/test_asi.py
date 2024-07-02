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

# Standard Library Imports
import unittest
from unittest.mock import Mock
import time

# Third Party Imports

# Local Imports
from navigate.model.devices.filter_wheel.asi import ASIFilterWheel


class TestASIFilterWheel(unittest.TestCase):
    def setUp(self):
        self.speed = 2
        self.number_of_filter_wheels = 2
        self.filter_wheel_delay = 0.5
        self.microscope_name = "mock_filter_wheel"
        self.mock_configuration = {
            "filter_wheel_delay": self.filter_wheel_delay,
            "hardware": {"wheel_number": self.number_of_filter_wheels},
            "available_filters": {
                "filter1": 0,
                "filter2": 1,
                "filter3": 2,
                "filter4": 3,
                "filter5": 4,
                "filter6": 5,
            },
        }

        # Mock Device Connection
        self.mock_device_connection = Mock()
        self.mock_device_connection.select_filter_wheel()
        self.mock_device_connection.move_filter_wheel()
        self.mock_device_connection.move_filter_wheel_to_home()
        self.mock_device_connection.disconnect_from_serial()
        self.mock_device_connection.is_open()
        self.mock_device_connection.is_open.return_value = True

        self.filter_wheel = ASIFilterWheel(
            device_connection=self.mock_device_connection,
            device_config=self.mock_configuration,
        )

    def test_init(self):
        self.assertEqual(self.filter_wheel.filter_wheel, self.mock_device_connection)
        self.assertEqual(
            self.filter_wheel.filter_wheel_number, self.number_of_filter_wheels
        )
        self.assertEqual(
            self.filter_wheel.wait_until_done_delay, self.filter_wheel_delay
        )
        self.assertEqual(self.filter_wheel.filter_wheel_position, 0)

    def test_init_sends_filter_wheels_to_zeroth_position(self):
        self.mock_device_connection.select_filter_wheel.assert_called()
        self.assertEqual(self.filter_wheel.wheel_position, 0)

    def test_filter_change_delay(self):
        # Current position
        self.filter_wheel.filter_wheel_position = 0

        # Position to move to
        filter_to_move_to = "filter4"
        self.filter_wheel.filter_change_delay(filter_to_move_to)
        self.assertEqual(self.filter_wheel.wait_until_done_delay, (3 * 0.04))

    def test_set_filter_does_not_exist(self):
        self.mock_device_connection.reset_mock()
        with self.assertRaises(ValueError):
            self.filter_wheel.set_filter("magic")

    def test_set_filter_without_waiting(self):
        self.mock_device_connection.reset_mock()
        delta = 4
        self.filter_wheel.set_filter(
            list(self.filter_wheel.filter_dictionary.keys())[0]
        )
        start_time = time.time()
        self.filter_wheel.set_filter(
            list(self.filter_wheel.filter_dictionary.keys())[delta],
            wait_until_done=False,
        )
        actual_duration = time.time() - start_time
        if_wait_duration = (delta - 1) * 0.04
        self.assertGreater(if_wait_duration, actual_duration)

    def test_close(self):
        self.mock_device_connection.reset_mock()
        self.filter_wheel.close()
        self.filter_wheel.filter_wheel.move_filter_wheel_to_home.assert_called()
        self.filter_wheel.filter_wheel.is_open.assert_called()


if __name__ == "__main__":
    unittest.main()
