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

# Standard library imports
import unittest
from unittest.mock import MagicMock
import multiprocessing

# Third party imports

# Local application imports
from navigate.model.device_startup_functions import auto_redial, start_device


class TestAutoRedial(unittest.TestCase):
    """Test the auto_redial function."""

    def test_successful_connection_first_try(self):
        """Test successful connection on the first try."""
        mock_func = MagicMock(return_value="success")
        result = auto_redial(mock_func, ())
        self.assertEqual(result, "success")

    def test_successful_connection_after_failures(self):
        """Test successful connection after a few failures."""
        mock_func = MagicMock(
            side_effect=[
                Exception("fail"),
                Exception("fail"),
                "success",
                Exception("fail"),
                "success",
            ]
        )
        result = auto_redial(mock_func, (), n_tries=5)
        self.assertEqual(result, "success")
        assert mock_func.call_count == 3

    def test_failure_after_all_retries(self):
        """Test failure after all retries."""
        mock_func = MagicMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            auto_redial(mock_func, (), n_tries=3)
        assert mock_func.call_count == 3

    def test_exception_type_handling(self):
        """Test that only the specified exception type is caught."""
        mock_func = MagicMock(side_effect=[ValueError("wrong exception"), "success"])
        with self.assertRaises(ValueError):
            auto_redial(mock_func, (), n_tries=3, exception=TypeError)
        assert mock_func.call_count == 1

    def test_arguments_passing(self):
        """Test that arguments and keyword arguments are correctly passed."""
        mock_func = MagicMock()
        auto_redial(mock_func, (1, 2), n_tries=1, kwarg1="test")
        mock_func.assert_called_with(1, 2, kwarg1="test")

    def test_start_device_plugin(self):
        """Test start_device_plugin behavior within auto_redial."""
        for device_category in [
            "camera",
            "shutter",
            "remote_focus",
            "zoom",
            "filter_wheel",
            "stage",
            "laser",
            "galvo",
        ]:
            if "_" in device_category:
                device_type = "".join(
                    [part.capitalize() for part in device_category.split("_")]
                )
            else:
                device_type = device_category.capitalize()

            device_class_name = f"Test{device_type}"

            plugin_devices = {
                device_category: {
                    device_class_name: {
                        "load_device": MagicMock(
                            return_value=f"test_{device_category}_connection"
                        ),
                        "start_device": MagicMock(
                            return_value=f"Test{device_type}Instance"
                        ),
                    }
                },
            }
            with multiprocessing.Manager() as manager:
                if device_category in ["camera", "shutter", "remote_focus", "zoom"]:
                    configuration = {
                        "configuration": {
                            "microscopes": {
                                "TestMicroscope": {
                                    device_category: {
                                        "hardware": {
                                            "type": device_class_name,
                                        }
                                    }
                                }
                            }
                        }
                    }
                    device_id = -1
                elif device_category == "stage":
                    proxy_list = manager.list(
                        [
                            {
                                "type": device_class_name,
                                "connection": "test_connection_string",
                            }
                        ]
                    )
                    configuration = {
                        "configuration": {
                            "microscopes": {
                                "TestMicroscope": {
                                    device_category: {"hardware": proxy_list}
                                }
                            }
                        }
                    }
                    device_id = 0
                else:
                    proxy_list = manager.list(
                        [
                            {
                                "hardware": {
                                    "type": device_class_name,
                                    "connection": "test_connection_string",
                                }
                            }
                        ]
                    )
                    configuration = {
                        "configuration": {
                            "microscopes": {
                                "TestMicroscope": {device_category: proxy_list}
                            }
                        }
                    }
                    device_id = 0

                if device_id == -1:
                    hardware_config = configuration["configuration"]["microscopes"][
                        "TestMicroscope"
                    ][device_category]["hardware"]
                elif device_category == "stage":
                    hardware_config = configuration["configuration"]["microscopes"][
                        "TestMicroscope"
                    ][device_category]["hardware"][device_id]
                else:
                    hardware_config = configuration["configuration"]["microscopes"][
                        "TestMicroscope"
                    ][device_category][device_id]["hardware"]

                r = start_device(
                    "TestMicroscope",
                    configuration,
                    device_category,
                    device_id,
                    False,
                    None,
                    plugin_devices,
                )
                assert r == f"{device_class_name}Instance"
                plugin_devices[device_category][device_class_name][
                    "load_device"
                ].assert_called_once()
                plugin_devices[device_category][device_class_name][
                    "load_device"
                ].assert_called_with(
                    hardware_config,
                    is_synthetic=False,
                    device_type=device_category,
                )
                plugin_devices[device_category][device_class_name][
                    "start_device"
                ].assert_called_once()
