# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

from multiprocessing import Manager

import pytest

from navigate.controller.configuration_controller import ConfigurationController


@pytest.fixture
def configuration():
    return {
        "experiment": {"MicroscopeState": {"microscope_name": "scope_a"}},
        "configuration": {
            "microscopes": {
                "scope_a": {
                    "galvo": [],
                    "filter_wheel": [
                        {
                            "hardware": {
                                "type": "Sutter",
                                "name": "Wheel A",
                                "wheel_number": 0,
                            }
                        },
                        {
                            "hardware": {
                                "type": "SyntheticFilterWheel",
                                "name": "Wheel B",
                                "wheel_number": 1,
                            }
                        },
                    ],
                },
                "scope_b": {
                    "galvo": [],
                    "filter_wheel": [
                        {
                            "hardware": {
                                "type": "ASI",
                                "name": "Wheel C",
                                "wheel_number": 0,
                            }
                        }
                    ],
                },
            }
        },
        "gui": {"channel_settings": {"count": 5}},
    }


def test_filter_wheel_types(configuration):
    controller = ConfigurationController(configuration)

    assert controller.filter_wheel_types == ["Sutter", "SyntheticFilterWheel"]


def test_gui_settings_are_read_from_gui_configuration(configuration):
    controller = ConfigurationController(configuration)

    assert controller.number_of_channels == 5
    assert controller.gui_setting is configuration["gui"]


@pytest.mark.parametrize("visibility", [None, "invalid", [True]])
def test_filter_wheel_visibility_defaults_to_all_true(configuration, visibility):
    if visibility is not None:
        configuration["configuration"]["microscopes"]["scope_a"][
            "filter_wheel_visibility"
        ] = visibility

    controller = ConfigurationController(configuration)

    assert controller.filter_wheel_visibility == [True, True]


def test_filter_wheel_visibility_boolean_cast(configuration):
    configuration["configuration"]["microscopes"]["scope_a"][
        "filter_wheel_visibility"
    ] = [1, 0]

    controller = ConfigurationController(configuration)

    assert controller.filter_wheel_visibility == [True, False]


def test_filter_wheel_visibility_listproxy(configuration):
    with Manager() as manager:
        configuration["configuration"]["microscopes"]["scope_a"][
            "filter_wheel_visibility"
        ] = manager.list([1, 0])

        controller = ConfigurationController(configuration)

        assert controller.filter_wheel_visibility == [True, False]


def test_change_microscope_logs_warning_for_missing_name(configuration, caplog):
    controller = ConfigurationController(configuration)

    with caplog.at_level("WARNING", logger="navigate"):
        result = controller.change_microscope("missing_scope")

    assert result is False
    assert controller.microscope_name == "scope_a"
    assert "Microscope missing_scope not found in configuration." in caplog.text
    assert "scope_a" in caplog.text
    assert "scope_b" in caplog.text
