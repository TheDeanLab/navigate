# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from navigate.model.devices.filter_wheel.sutter import SutterFilterWheel


class TestSutterFilterWheel(unittest.TestCase):
    def setUp(self):
        self.mock_device_connection = Mock()
        self.mock_device_connection.read.return_value = b"00"
        self.mock_device_connection.inWaiting.return_value = 2
        self.mock_device_connection.write.return_value = None
        self.mock_device_connection.set_filter()
        self.mock_device_connection.close()

        self.speed = 2
        self.number_of_filter_wheels = 2
        self.microscope_name = "mock_filter_wheel"
        self.mock_configuration = {
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

        self.filter_wheel = SutterFilterWheel(
            device_connection=self.mock_device_connection,
            device_config=self.mock_configuration,
        )

    def test_init(self):
        self.assertEqual(self.filter_wheel.serial, self.mock_device_connection)
        self.assertEqual(
            self.filter_wheel.filter_wheel_number, self.number_of_filter_wheels
        )
        self.assertEqual(self.filter_wheel.wait_until_done, True)
        self.assertEqual(self.filter_wheel.read_on_init, True)
        self.assertEqual(self.filter_wheel.speed, self.speed)

    def test_init_sends_filter_wheels_to_zeroth_position(self):
        self.mock_device_connection.write.assert_called()
        self.mock_device_connection.set_filter.assert_called()
        self.assertEqual(self.filter_wheel.wheel_position, 0)

    def test_filter_wheel_delay(self):
        for delta in range(6):
            self.filter_wheel.set_filter(
                list(self.filter_wheel.filter_dictionary.keys())[0]
            )
            self.filter_wheel.set_filter(
                list(self.filter_wheel.filter_dictionary.keys())[delta]
            )
            self.assertEqual(
                self.filter_wheel.wait_until_done_delay,
                self.filter_wheel.delay_matrix[self.speed, delta],
            )

    def test_set_filter_does_not_exist(self):
        self.mock_device_connection.reset_mock()
        with self.assertRaises(ValueError):
            self.filter_wheel.set_filter("magic")

    def test_set_filter_init_not_finished(self):
        self.mock_device_connection.reset_mock()
        self.filter_wheel.init_finished = False
        self.filter_wheel.set_filter(
            list(self.filter_wheel.filter_dictionary.keys())[2]
        )
        self.mock_device_connection.read.assert_called()
        self.filter_wheel.init_finished = True

    def test_set_filter_init_finished(self):
        for wait_flag, read_num in [(True, 2), (False, 1)]:
            self.mock_device_connection.reset_mock()
            self.filter_wheel.init_finished = True
            read_count = 0
            for i in range(6):
                self.filter_wheel.set_filter(
                    list(self.filter_wheel.filter_dictionary.keys())[i],
                    wait_until_done=wait_flag,
                )
                self.mock_device_connection.write.assert_called()
                self.mock_device_connection.read.assert_called()
                read_count += read_num
                assert self.mock_device_connection.read.call_count == read_count

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
        if_wait_duration = self.filter_wheel.delay_matrix[self.speed, delta]
        self.assertGreater(if_wait_duration, actual_duration)

    def test_read_wrong_number_bytes_returned(self):
        self.mock_device_connection.reset_mock()
        # fewer response bytes than expected
        with self.assertRaises(UserWarning):
            # in_waiting() returns an integer.
            self.mock_device_connection.inWaiting.return_value = 1
            self.filter_wheel.read(num_bytes=10)
        # more response bytes than expected
        self.mock_device_connection.inWaiting.return_value = 12
        self.filter_wheel.read(num_bytes=10)

    def test_read_correct_number_bytes_returned(self):
        # Mocked device connection expected to return 2 bytes
        self.mock_device_connection.reset_mock()
        number_bytes = 2
        self.mock_device_connection.reset_mock()
        self.mock_device_connection.inWaiting.return_value = number_bytes
        returned_bytes = self.filter_wheel.read(num_bytes=number_bytes)
        self.assertEqual(len(returned_bytes), number_bytes)

    def test_close(self):
        self.mock_device_connection.reset_mock()
        self.filter_wheel.close()
        self.mock_device_connection.close.assert_called()

    def test_exit(self):
        self.mock_device_connection.reset_mock()
        del self.filter_wheel
        self.mock_device_connection.close.assert_called()


if __name__ == "__main__":
    unittest.main()
