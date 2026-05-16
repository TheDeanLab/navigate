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

"""Thorlabs Kinesis controller wrapper backed by pylablib."""

import logging
from time import sleep
from typing import Any

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

SLEEP_AFTER_WAIT = 0.100


class KinesisStage:
    """Simple wrapper around pylablib's Kinesis motor API."""

    def __init__(self, dev_path: str, verbose: bool = False):
        self.verbose = verbose
        self.dev_path = str(dev_path)
        self.stage = None
        self.move_params: dict[str, float] = {
            "min_velocity": 0.0,
            "max_velocity": 0.0,
            "acceleration": 0.0,
        }
        self.open()

    @staticmethod
    def _load_thorlabs_backend() -> Any:
        """Load pylablib Thorlabs backend lazily."""
        try:
            from pylablib.devices import Thorlabs
        except ImportError as e:
            raise ImportError("pylablib is required for KINESIS stage support.") from e
        return Thorlabs

    def open(self) -> None:
        """Open the device for communications."""
        thorlabs = self._load_thorlabs_backend()
        connection = {"port": self.dev_path, "baudrate": 115200, "rtscts": True}
        try:
            self.stage = thorlabs.KinesisMotor(("serial", connection), scale="step")
        except Exception as e:
            raise ConnectionError(f"KINESIS stage connection failed: {e}") from e

    def close(self) -> None:
        """Disconnect and close the device."""
        if self.stage is None:
            return
        try:
            self.stage.stop()
        except Exception as exc:
            logger.debug(
                "Failed to stop KINESIS stage cleanly during close: %s",
                exc,
                exc_info=True,
            )
        self.stage.close()

    def move_to_position(
        self, position_um: float, steps_per_um: float, wait_till_done: bool
    ) -> None:
        """Move to absolute position in microns."""
        current_steps = self.stage.get_position(channel=1, scale=False)
        target_steps = int(round(float(position_um) * float(steps_per_um)))
        delta_steps = target_steps - int(current_steps)
        self.stage.move_by(delta_steps, channel=1, scale=False)
        if wait_till_done:
            self.stage.wait_move(channel=1)
            if SLEEP_AFTER_WAIT:
                sleep(SLEEP_AFTER_WAIT)

    def get_current_position(self, steps_per_um: float) -> float:
        """Get current position in microns."""
        current_steps = self.stage.get_position(channel=1, scale=False)
        position_um = float(current_steps) / float(steps_per_um)
        return round(position_um, 2)

    def stop(self) -> None:
        """Halt motion."""
        self.stage.stop()

    def home_stage(self) -> None:
        """Run homing sequence."""
        self.stage.home()

    def set_velocity_params(
        self,
        min_velocity: float,
        max_velocity: float,
        acceleration: float,
        steps_per_um: float,
    ) -> None:
        """Set motion profile parameters."""
        min_velocity_steps = min_velocity * steps_per_um
        max_velocity_steps = max_velocity * steps_per_um
        acceleration_steps = acceleration * steps_per_um
        self.stage.set_move_params(
            min_velocity_steps, max_velocity_steps, acceleration_steps
        )
        self.move_params = {
            "min_velocity": min_velocity_steps,
            "max_velocity": max_velocity_steps,
            "acceleration": acceleration_steps,
        }
