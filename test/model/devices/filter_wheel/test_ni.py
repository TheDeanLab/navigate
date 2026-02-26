# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
from unittest.mock import Mock, patch


from navigate.model.devices.filter_wheel.ni import NIFilterWheel


class TestNIFilterWheel(unittest.TestCase):
    def setUp(self):
        # self.mock_task = Mock()
        self.mock_device_connection = Mock()
        # self.mock_device_connection.create_task.return_value = self.mock_task

        configuration = {
            "configuration": {
                "microscopes": {
                    "TestScope": {
                        "filter_wheel": [
                            {
                                "available_filters": {
                                    "filter_1": "Channel/line0",
                                    "filter_2": "Channel/line0",
                                },
                                "hardware": {
                                    "type": "NI",
                                    "wheel_number": 1,
                                },
                                "filter_wheel_delay": 0.5,
                            },
                            {
                                "available_filters": {
                                    "filter_3": "Channel/line1",
                                    "filter_4": "Channel/line1",
                                },
                                "hardware": {
                                    "type": "NI",
                                    "wheel_number": 2,
                                },
                                "filter_wheel_delay": 0.5,
                            },
                        ]
                    }
                }
            }
        }

        self.filter_wheel = NIFilterWheel(
            microscope_name="TestScope",
            device_connection=self.mock_device_connection,
            configuration=configuration,
            device_id=0,
        )

        self.filter_wheel_2 = NIFilterWheel(
            microscope_name="TestScope",
            device_connection=self.mock_device_connection,
            configuration=configuration,
            device_id=1,
        )

    @patch("navigate.model.devices.filter_wheel.ni.nidaqmx.Task")
    def test_set_filter_valid(self, mock_task):
        self.filter_wheel.set_filter("filter_1")
        assert mock_task.called_once()
        self.assertEqual(self.filter_wheel.filter_wheel_value[1], "filter_1")

        # set to the same value again, should not call write
        mock_task.reset_mock()
        self.filter_wheel.set_filter("filter_1")
        mock_task.write.assert_not_called()

        # set to a different value
        self.filter_wheel.set_filter("filter_2")
        self.assertEqual(self.filter_wheel.filter_wheel_value[1], "filter_2")
        assert mock_task.called_once()

        # set to the same value again, should not call write
        mock_task.reset_mock()
        self.filter_wheel.set_filter("filter_2")
        mock_task.write.assert_not_called()

    def test_set_filter_invalid(self):
        with self.assertRaises(ValueError):
            self.filter_wheel.set_filter(-1)

    @patch("navigate.model.devices.filter_wheel.ni.nidaqmx.Task")
    def test_multiple_filter_wheels_independent(self, mock_task):
        self.filter_wheel.set_filter("filter_1")
        self.filter_wheel_2.set_filter("filter_3")

        self.assertEqual(self.filter_wheel.filter_wheel_value[1], "filter_1")
        self.assertEqual(self.filter_wheel_2.filter_wheel_value[2], "filter_3")

        self.filter_wheel_2.set_filter("filter_4")
        self.assertEqual(self.filter_wheel.filter_wheel_value[1], "filter_1")
        self.assertEqual(self.filter_wheel_2.filter_wheel_value[2], "filter_4")
