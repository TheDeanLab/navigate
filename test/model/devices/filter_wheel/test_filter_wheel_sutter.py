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

import pytest
import unittest
from unittest.mock import Mock
from aslm.model.devices.filter_wheel.filter_wheel_sutter import SutterFilterWheel


@pytest.mark.hardware
def test_filter_wheel_sutter_init():
    from aslm.model.devices.filter_wheel.filter_wheel_sutter import (
        SutterFilterWheel,
        build_filter_wheel_connection,
    )
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    if (
        model.configuration["configuration"]["hardware"]["filter_wheel"]["type"]
        != "SutterFilterWheel"
    ):
        raise TypeError(
            "Wrong filter wheel hardware specified."
            # f"{model.configuration['configuration']['hardware']['filter_wheel'][
            # 'type'] != 'SutterFilterWheel'}"
        )
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]

    serial_controller = build_filter_wheel_connection(
        model.configuration["configuration"]["hardware"]["filter_wheel"]["port"],
        model.configuration["configuration"]["hardware"]["filter_wheel"]["baudrate"],
    )

    SutterFilterWheel(microscope_name, serial_controller, model.configuration)


#
# @pytest.mark.hardware
# def test_filter_wheel_sutter_functions():
#     import random
#
#     from aslm.model.devices.filter_wheel.filter_wheel_sutter import (
#         SutterFilterWheel,
#         build_filter_wheel_connection,
#     )
#     from aslm.model.dummy import DummyModel
#
#     model = DummyModel()
#     if (
#         model.configuration["configuration"]["hardware"]["filter_wheel"]["type"]
#         != "SutterFilterWheel"
#     ):
#         raise TypeError(
#             f"Wrong filter wheel hardware specified {
#         model.configuration['configuration']['hardware']['filter_wheel']['type']
#             }} is not SutterFilterWheel")
#     model.configuration["experiment"]["MicroscopeState"][
#         "microscope_name"
#     ]
#
#     build_filter_wheel_connection(
#         model.configuration["configuration"]["hardware"]["filter_wheel"]["port"],
#         model.configuration["configuration"]["hardware"]["filter_wheel"]["baudrate"],
#     )
#
#     fw = SutterFilterWheel(microscope_name, serial_controller, model.configuration)
#     filter_names = [
#         x for x in list(fw.filter_dictionary.keys()) if not x.startswith("Blocked")
#     ]
#     n_filters = len(filter_names) - 1
#
#     print(filter_names)
#     print(n_filters)
#
#     funcs = ["filter_change_delay", "set_filter", "close"]
#     args = [
#         [filter_names[random.randint(0, n_filters)]],
#         [filter_names[random.randint(0, n_filters)]],
#         None,
#     ]
#
#     for f, a in zip(funcs, args):
#         if a is not None:
#             getattr(fw, f)(*a)
#         else:
#             getattr(fw, f)()


class TestSutterFilterWheel(unittest.TestCase):
    def setUp(self):
        self.mock_device_connection = Mock()
        self.mock_device_connection.read.return_value = b"00"
        self.mock_device_connection.inWaiting.return_value = 2
        self.mock_device_connection.write.return_value = None

        self.number_of_filter_wheels = 2
        self.microscope_name = "mock_filter_wheel"

        self.mock_configuration = {
            "configuration": {
                "microscopes": {
                    self.microscope_name: {
                        "filter_wheel": {
                            "hardware": {"wheel_number": self.number_of_filter_wheels},
                            "filter_wheel_delay": 0.5,
                            "available_filters": {
                                "filter1": 0,
                                "filter2": 1,
                                "filter3": 2,
                                "filter4": 3,
                                "filter5": 4,
                                "filter6": 5,
                            },
                        }
                    }
                }
            }
        }
        self.mock_filter_wheel = SutterFilterWheel(
            microscope_name=self.microscope_name,
            device_connection=self.mock_device_connection,
            configuration=self.mock_configuration,
        )

    def test_init(self):
        self.assertEqual(self.mock_filter_wheel.serial, self.mock_device_connection)

        self.assertEqual(self.microscope_name, self.mock_filter_wheel.microscope_name)
        self.assertEqual(
            self.mock_filter_wheel.number_of_filter_wheels, self.number_of_filter_wheels
        )
        self.assertEqual(self.mock_filter_wheel.wait_until_done, True)
        self.assertEqual(self.mock_filter_wheel.read_on_init, True)
        self.assertEqual(self.mock_filter_wheel.speed, 2)

    def test_init_sends_filter_wheels_to_zeroth_position(self):
        default_filter = "filter1"
        self.mock_filter_wheel.set_filter(filter_name=default_filter)
        self.mock_device_connection.write.assert_called()

    def test_filter_wheel_delay(self):
        self.mock_filter_wheel.set_filter(
            list(self.mock_filter_wheel.filter_dictionary.keys())[0]
        )
        self.mock_filter_wheel.set_filter(
            list(self.mock_filter_wheel.filter_dictionary.keys())[1]
        )
        self.assertEqual(self.mock_filter_wheel.wait_until_done_delay, 0.044)

    def test_set_filter(self):
        self.mock_device_connection.reset_mock()
        for i in range(6):
            self.mock_filter_wheel.set_filter(
                list(self.mock_filter_wheel.filter_dictionary.keys())[i]
            )
            self.mock_device_connection.write.assert_called()
            self.mock_device_connection.read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
