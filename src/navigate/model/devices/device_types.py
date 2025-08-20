# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
from abc import ABC, abstractmethod
import time
import json
import logging
from typing import Union

# Third Party Imports
import serial

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class DeviceBase(ABC):
    """DeviceBase - Parent device class."""

    def __init__(
        self,
        device_name: str,
        *args,
        **kwargs,
    ) -> None:
        """Initialize DeviceBase class.

        Parameters
        ----------
        device_name : str
            Name of the device, used as a unique identifier.
        """
        #: str: Name of the device, used as a unique identifier.
        self.device_name = device_name

        #: str: Unique identifier for the device, typically the device name.
        self.unique_id = device_name

        #: object: Connection object for the device, initialized to None.
        self.device_connection = None

    @abstractmethod
    def connect(self) -> None:
        """Connect to the device."""
        pass


class MonitoredSerial:
    """MonitoredSerial - Serial class that logs read/write events."""

    def __init__(self, serial_connection: serial.Serial):
        """Initialize MonitoredSerial with an existing connection, without initializing a new serial.Serial instance.

        Parameters
        ----------
        serial_connection : serial.Serial
            An existing serial connection to wrap
        """
        self.serial = serial_connection

    def write(self, data: bytes):
        """Write data to the serial port and log the event.

        Parameters
        ----------
        data : bytes
            Data to be written to the serial port.
        """

        start = time.perf_counter_ns()
        self.serial.write(data)
        self.log_event("write", data, time.perf_counter_ns() - start)

    def readline(self, size: Union[int, None] = -1, /) -> bytes:
        """Read a line from the serial port and log the event.

        Parameters
        ----------
        size : int, optional
            The maximum number of bytes to read, by default -1 (read until timeout).

        Returns
        -------
        bytes
            The line read from the serial port.
        """
        start = time.perf_counter_ns()
        line = self.serial.readline()
        self.log_event("readline", line, time.perf_counter_ns() - start)
        return line

    def read(self, size: int = 1) -> bytes:
        """Read a specified number of bytes from the serial port and log the event.

        Parameters
        ----------
        size : int, optional
            The number of bytes to read, by default 1.

        Returns
        -------
        bytes
            The bytes read from the serial port.
        """
        start = time.perf_counter_ns()
        data = self.serial.read(size)
        self.log_event("read", data, time.perf_counter_ns() - start)
        return data

    @property
    def in_waiting(self) -> int:
        return self.serial.in_waiting
    
    @property
    def is_open(self) -> bool:
        return self.serial.is_open

    @staticmethod
    def log_event(kind: str, payload: bytes, duration_ns: int) -> None:
        """Log the read/write event with performance data.

        Parameters
        ----------
        kind : str
            The type of event, either "read" or "write".
        payload : bytes
            The data that was read or written.
        duration_ns : int
            The duration of the read/write operation in nanoseconds.
        """
        logger.performance(
            json.dumps(
                {
                    "kind": kind,
                    "payload": payload.decode(errors="ignore"),
                    "duration_ns": duration_ns,
                    "timestamp": time.time(),
                }
            )
        )



class SerialDevice:
    """SerialDevice - Parent serial device class."""

    def __init__(
        self,
        device_name: str,
        port: str = "",
        baudrate: int = 115200,
        timeout: float = 0.25,
        **kwargs,
    ) -> None:
        """Initialize SerialDevice class.

        Parameters
        ----------
        device_name : str
            Name of the device, used as a unique identifier.
        port : str, optional
            Serial port to connect to the device, by default an empty string.
        baudrate : int, optional
            Baud rate for the serial connection, by default 115200.
        timeout : float, optional
            Timeout for the serial connection in seconds, by default 0.25.
        """

        #: str: Name of the device, used as a unique identifier.
        self.device_name = device_name

        #: str: Unique identifier for the device, serial_ followed by the port.
        self.unique_id = "serial_" + port

    def connect(
        self, port: str, baudrate: int = 115200, timeout: float = 0.25
    ) -> object:
        """Connect to serial device.

        Parameters
        ----------
        port : str
            Serial port to connect to the device.
        baudrate : int, optional
            Baud rate for the serial connection, by default 115200.
        timeout : float, optional
            Timeout for the serial connection in seconds, by default 0.25.

        Returns
        -------
        serial.Serial
            The serial connection object if successful, otherwise None.
        """
        if port:
            from serial import Serial

            self.serial = Serial()
            self.serial.port = port
            self.serial.baudrate = baudrate
            self.serial.timeout = timeout
            self.serial.open()
        else:
            self.serial = None

        return self.serial

    def disconnect(self) -> None:
        """Disconnect from serial device."""
        try:
            if self.serial.is_open:
                self.serial.close()
        except Exception as e:
            print(f"Error disconnecting from serial device: {e}")


class IntegratedDevice:
    """IntegratedDevice - Parent integrated device class."""


class NIDevice:
    """NIDevice - Parent National Instruments device class."""


class SequenceDevice:
    """SequenceDevice - The device loaded according to its sequence id, not serial number.
    Always need to check if the serial number is match.
    """
