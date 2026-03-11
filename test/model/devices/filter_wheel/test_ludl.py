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

from unittest.mock import MagicMock, patch

import pytest
import serial

from navigate.model.devices.filter_wheel.ludl import LUDLFilterWheel


def build_configuration() -> dict:
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "filter_wheel": [
                        {
                            "available_filters": {"empty": 0, "gfp": 1, "dapi": 2},
                            "hardware": {"wheel_number": 1},
                            "filter_wheel_delay": 0.1,
                        }
                    ]
                }
            }
        }
    }


def build_filter_wheel():
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.close.side_effect = lambda: setattr(mock_serial, "is_open", False)
    mock_sio = MagicMock()

    with patch(
        "navigate.model.devices.filter_wheel.ludl.io.BufferedRWPair",
        return_value=object(),
    ), patch(
        "navigate.model.devices.filter_wheel.ludl.io.TextIOWrapper",
        return_value=mock_sio,
    ):
        filter_wheel = LUDLFilterWheel(
            microscope_name="TestScope",
            device_connection=mock_serial,
            configuration=build_configuration(),
            device_id=0,
        )

    return filter_wheel, mock_serial, mock_sio


def test_connect_success():
    mock_serial = MagicMock()

    with patch(
        "navigate.model.devices.filter_wheel.ludl.serial.Serial",
        return_value=mock_serial,
    ) as serial_ctor:
        result = LUDLFilterWheel.connect("COM1", baudrate=19200, timeout=1.25)

    assert result is mock_serial
    serial_ctor.assert_called_once_with(
        "COM1",
        19200,
        parity=serial.PARITY_NONE,
        timeout=1.25,
        xonxoff=False,
        stopbits=serial.STOPBITS_TWO,
    )


def test_connect_failure_raises_user_warning():
    with patch(
        "navigate.model.devices.filter_wheel.ludl.serial.Serial",
        side_effect=serial.SerialException,
    ):
        with pytest.raises(UserWarning, match="Could not communicate"):
            LUDLFilterWheel.connect("COM2")


def test_set_filter_with_wait():
    filter_wheel, _, mock_sio = build_filter_wheel()

    with patch("navigate.model.devices.filter_wheel.ludl.time.sleep") as sleep:
        filter_wheel.set_filter("gfp", wait_until_done=True)

    assert filter_wheel.wheel_position == 1
    mock_sio.write.assert_called_once_with("Rotat S M 1\n")
    mock_sio.flush.assert_called_once()
    sleep.assert_called_once_with(0.1)


def test_set_filter_without_wait():
    filter_wheel, _, mock_sio = build_filter_wheel()

    with patch("navigate.model.devices.filter_wheel.ludl.time.sleep") as sleep:
        filter_wheel.set_filter("dapi", wait_until_done=False)

    assert filter_wheel.wheel_position == 2
    mock_sio.write.assert_called_once_with("Rotat S M 2\n")
    mock_sio.flush.assert_called_once()
    sleep.assert_not_called()


def test_set_filter_invalid_name_raises():
    filter_wheel, _, mock_sio = build_filter_wheel()

    with pytest.raises(ValueError, match="Unknown filter name"):
        filter_wheel.set_filter("not_real")

    mock_sio.write.assert_not_called()
    mock_sio.flush.assert_not_called()


def test_close_sets_first_filter_then_closes_serial():
    filter_wheel, mock_serial, mock_sio = build_filter_wheel()

    with patch("navigate.model.devices.filter_wheel.ludl.time.sleep"):
        filter_wheel.close()

    mock_sio.write.assert_called_once_with("Rotat S M 0\n")
    mock_sio.flush.assert_called_once()
    mock_serial.close.assert_called_once()


def test_del_closes_when_serial_is_open():
    filter_wheel, _, _ = build_filter_wheel()
    filter_wheel.close = MagicMock()
    filter_wheel.serial.is_open = True

    filter_wheel.__del__()

    filter_wheel.close.assert_called_once()


def test_del_does_not_close_when_serial_closed():
    filter_wheel, _, _ = build_filter_wheel()
    filter_wheel.close = MagicMock()
    filter_wheel.serial.is_open = False

    filter_wheel.__del__()

    filter_wheel.close.assert_not_called()
