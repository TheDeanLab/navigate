"""Hardware devices."""

# Standard library imports
import time
from typing import Union
import json
import logging

# Third party imports
import serial

# Local imports
from .daq.synthetic import SyntheticDAQ  # noqa
from .camera.synthetic import SyntheticCamera  # noqa
from .filter_wheel.synthetic import SyntheticFilterWheel  # noqa
from .galvo.synthetic import SyntheticGalvo  # noqa
from .remote_focus.synthetic import SyntheticRemoteFocus  # noqa
from .shutter.synthetic import SyntheticShutter  # noqa
from .stage.synthetic import SyntheticStage  # noqa
from .zoom.synthetic import SyntheticZoom  # noqa
from .laser.synthetic import SyntheticLaser  # noqa
from .mirror.synthetic import SyntheticMirror  # noqa

logger = logging.getLogger(__name__.split(".")[1])


class MonitoredSerial(serial.Serial):
    """MonitoredSerial - Serial class that logs read/write events."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write(self, data: bytes):
        """Write data to the serial port and log the event.

        Parameters
        ----------
        data : bytes
            Data to be written to the serial port.
        """

        start = time.perf_counter_ns()
        super().write(data)
        self.log_event(data, time.perf_counter_ns() - start)

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
        line = super().readline()
        self.log_event(line, time.perf_counter_ns() - start)
        return line

    def read(self, size=1) -> bytes:
        """Read bytes from the serial port and log the event.

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
        data = super().read(size)
        self.log_event(data, time.perf_counter_ns() - start)
        return data

    def log_event(self, payload: bytes, duration_ns: int) -> None:
        """Log the read/write event with performance data.

        Parameters
        ----------
        payload : bytes
            The data that was read or written.
        duration_ns : int
            The duration of the read/write operation in nanoseconds.
        """
        logger.performance(
            json.dumps(
                {
                    "kind": "Serial",
                    "payload": payload.decode(errors="ignore"),
                    "duration_ns": duration_ns,
                    "timestamp": time.time(),
                }
            )
        )
