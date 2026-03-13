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

import navigate.model.devices.device_types as device_types


class _DummyDevice(device_types.DeviceBase):
    def connect(self):
        self.device_connection = "connected"


def test_device_base_initializes_required_fields():
    device = _DummyDevice("demo-device")

    assert device.device_name == "demo-device"
    assert device.unique_id == "demo-device"
    assert device.device_connection is None


def test_device_base_abstract_connect_body_is_callable():
    device = _DummyDevice("demo-device")

    # Calling the abstract base implementation directly exercises its no-op body.
    assert device_types.DeviceBase.connect(device) is None


def test_serial_device_connect_without_port_returns_none():
    device = device_types.SerialDevice("serial-device")

    result = device.connect(port="")

    assert result is None
    assert device.serial is None
    assert device.unique_id == "serial_"


def test_serial_device_connect_with_port_opens_connection(monkeypatch):
    class FakeSerial:
        def __init__(self):
            self.port = None
            self.baudrate = None
            self.timeout = None
            self.is_open = False
            self.open_called = False
            self.close_called = False

        def open(self):
            self.open_called = True
            self.is_open = True

        def close(self):
            self.close_called = True
            self.is_open = False

    monkeypatch.setattr(device_types.serial, "Serial", FakeSerial)
    device = device_types.SerialDevice("serial-device")

    connection = device.connect(port="COM7", baudrate=9600, timeout=1.5)
    assert isinstance(connection, FakeSerial)
    assert connection.port == "COM7"
    assert connection.baudrate == 9600
    assert connection.timeout == 1.5
    assert connection.open_called is True

    device.disconnect()
    assert connection.close_called is True


def test_serial_device_disconnect_handles_connection_errors(capsys):
    class BrokenSerial:
        @property
        def is_open(self):
            raise RuntimeError("broken serial state")

    device = device_types.SerialDevice("serial-device")
    device.serial = BrokenSerial()

    device.disconnect()

    assert "Error disconnecting from serial device" in capsys.readouterr().out


def test_marker_device_classes_are_instantiable():
    assert isinstance(device_types.IntegratedDevice(), device_types.IntegratedDevice)
    assert isinstance(device_types.NIDevice(), device_types.NIDevice)
    assert isinstance(device_types.ASIDevice(), device_types.ASIDevice)
    assert isinstance(device_types.SequenceDevice(), device_types.SequenceDevice)
