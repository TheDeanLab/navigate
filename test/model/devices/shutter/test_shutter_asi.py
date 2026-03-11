# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
#

import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "navigate.model.devices.shutter.asi"
TIGER_MODULE_PATH = "navigate.model.devices.APIs.asi.asi_tiger_controller"


class _FakeTigerController:
    default_is_open = True

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connect_calls = 0
        self.disconnect_calls = 0
        self.logic_on_calls = []
        self.logic_off_calls = []
        self.axis_positions = {}
        self._is_open = type(self).default_is_open

    def connect_to_serial(self):
        self.connect_calls += 1

    def is_open(self):
        return self._is_open

    def disconnect_from_serial(self):
        self.disconnect_calls += 1

    def logic_card_on(self, axis):
        self.logic_on_calls.append(axis)

    def logic_card_off(self, axis):
        self.logic_off_calls.append(axis)

    def get_axis_position(self, axis):
        return self.axis_positions.get(axis, False)


@pytest.fixture
def asi_module(monkeypatch):
    _FakeTigerController.default_is_open = True
    fake_tiger_module = types.ModuleType(TIGER_MODULE_PATH)
    fake_tiger_module.TigerController = _FakeTigerController

    monkeypatch.setitem(sys.modules, TIGER_MODULE_PATH, fake_tiger_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)
    return module


@pytest.fixture
def shutter_config():
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {"shutter": {"hardware": {"axis": "A", "port": "COM9"}}}
            }
        }
    }


def test_connect_success(asi_module):
    controller = asi_module.ASIShutter.connect(port="COM5", baudrate=9600)

    assert isinstance(controller, _FakeTigerController)
    assert controller.port == "COM5"
    assert controller.baudrate == 9600
    assert controller.connect_calls == 1


def test_connect_raises_when_not_open(asi_module):
    _FakeTigerController.default_is_open = False

    with patch.object(asi_module.logger, "error") as mock_error:
        with pytest.raises(Exception, match="ASI shutter connection failed."):
            asi_module.ASIShutter.connect(port="COM5")

    mock_error.assert_called_once_with("ASI shutter connection failed.")


def test_asi_shutter_init_and_state(asi_module, shutter_config):
    device_connection = MagicMock()
    device_connection.get_axis_position.return_value = True

    shutter = asi_module.ASIShutter(
        microscope_name="TestScope",
        device_connection=device_connection,
        configuration=shutter_config,
        address="addr1",
    )

    assert shutter.axis == "A"
    assert shutter.port == "COM9"
    assert shutter.address == "addr1"
    assert shutter.shutter is device_connection
    assert shutter.state is True
    device_connection.get_axis_position.assert_called_once_with("A")

    shutter.shutter = None


def test_open_shutter_success_and_error(asi_module, shutter_config):
    device_connection = MagicMock()
    shutter = asi_module.ASIShutter("TestScope", device_connection, shutter_config)

    shutter.open_shutter()
    device_connection.logic_card_on.assert_called_once_with("A")

    device_connection.logic_card_on.side_effect = RuntimeError("open failed")
    with patch.object(asi_module.logger, "exception") as mock_exception:
        shutter.open_shutter()
    mock_exception.assert_called_once()

    shutter.shutter = None


def test_close_shutter_success_and_error(asi_module, shutter_config):
    device_connection = MagicMock()
    shutter = asi_module.ASIShutter("TestScope", device_connection, shutter_config)

    shutter.close_shutter()
    device_connection.logic_card_off.assert_called_once_with("A")

    device_connection.logic_card_off.side_effect = RuntimeError("close failed")
    with patch.object(asi_module.logger, "exception") as mock_exception:
        shutter.close_shutter()
    mock_exception.assert_called_once()

    shutter.shutter = None


def test_del_disconnects_when_shutter_present(asi_module, shutter_config):
    device_connection = MagicMock()
    shutter = asi_module.ASIShutter("TestScope", device_connection, shutter_config)

    shutter.__del__()
    device_connection.disconnect_from_serial.assert_called_once_with()
    shutter.shutter = None


def test_del_handles_disconnect_error(asi_module, shutter_config):
    device_connection = MagicMock()
    device_connection.disconnect_from_serial.side_effect = RuntimeError(
        "disconnect failed"
    )
    shutter = asi_module.ASIShutter("TestScope", device_connection, shutter_config)

    with patch.object(asi_module.logger, "exception") as mock_exception:
        shutter.__del__()

    mock_exception.assert_called_once()
    shutter.shutter = None


def test_del_is_noop_without_shutter(asi_module, shutter_config):
    device_connection = MagicMock()
    shutter = asi_module.ASIShutter("TestScope", device_connection, shutter_config)
    shutter.shutter = None

    shutter.__del__()
