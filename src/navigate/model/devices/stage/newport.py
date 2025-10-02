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

# This file has been adapted to control a Newport ESP302 stage
# by conforming to the host software's device architecture, using asi.py as a template.

# Standard Library Imports
import logging
import time
import telnetlib
from typing import Any, Dict

# Local Imports
try:
    from navigate.model.devices.stage.base import StageBase
    from navigate.model.devices.device_types import SerialDevice, IntegratedDevice
    from navigate.tools.decorators import log_initialization
except ImportError:
    # Dummy classes for standalone functionality if navigate is not available
    class StageBase:
        def __init__(self, *args, **kwargs):
            self.axes = ["x"]

        def get_position_dict(self):
            return {self.axes[0]: getattr(self, f"{self.axes[0]}_pos", 0.0)}

        def verify_abs_position(self, pos_dict):
            return pos_dict

    class SerialDevice:
        pass

    class IntegratedDevice:
        pass

    def log_initialization(func):
        return func


# Logger Setup
p = __name__.split(".")[-1]
logger = logging.getLogger(p)


# --- Newport ESP302 Specific API Logic ---


class NewportESP302Error(Exception):
    """Custom exception for ESP302 device errors."""

    pass


class NewportESP302API:
    """
    Handles low-level Telnet communication with the Newport ESP302 controller.
    This is analogous to the TigerController or MP285 class.
    """

    def __init__(
        self, host, port: int = 5001, timeout: int = 10, logger_func=logging.info
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logger = logger_func
        self.tn = None

    def connect(self):
        if self.tn:
            self.logger("Already connected.", "DEBUG")
            return True
        try:
            self.tn = telnetlib.Telnet(self.host, self.port, self.timeout)
            try:
                self.tn.read_until(b"\r\n", timeout=0.5)
            except EOFError:
                pass
            self.logger(
                f"Successfully connected to ESP302 at {self.host}:{self.port}", "INFO"
            )
            return True
        except Exception as e:
            self.tn = None
            self.logger(f"Connection failure: {e}", "ERROR")
            raise NewportESP302Error(
                f"Failed to connect to {self.host}:{self.port} - {e}"
            )

    def disconnect(self):
        if self.tn:
            try:
                self.tn.close()
            except Exception:
                pass
            self.tn = None
            self.logger("Disconnected from ESP302.", "INFO")

    def _send_and_read(self, command_str: str) -> str:
        if not self.tn:
            raise NewportESP302Error("Not connected to the controller.")
        # ESP302 commands are terminated with a single carriage return
        full_command_bytes = command_str.encode("ascii") + b"\r"
        self.logger(f"CMD > {command_str.strip()}", "DEBUG")
        try:
            self.tn.write(full_command_bytes)
            # The response is terminated with both carriage return and line feed
            response_bytes = self.tn.read_until(b"\r\n", timeout=self.timeout)
            response = response_bytes.decode("ascii").strip()
            self.logger(f"RSP < {response}", "DEBUG")
            return response
        except EOFError as e:
            self.disconnect()
            raise NewportESP302Error(f"Connection closed by controller: {e}")
        except Exception as e:
            raise NewportESP302Error(
                f"Telnet error during command '{command_str}': {e}"
            )

    def check_controller_error(self):
        """Queries the controller for the latest error and raises if one exists."""
        try:
            error_code_str = self._send_and_read("TE?")
            if error_code_str and error_code_str.isdigit() and int(error_code_str) != 0:
                raise NewportESP302Error(
                    f"ESP302 reported error code: {error_code_str}"
                )
        except NewportESP302Error as e:
            if "error code" in str(e).lower():
                raise
            else:
                self.logger(f"Could not check controller error: {e}", "WARNING")

    def get_position(self, axis: int) -> float:
        response = self._send_and_read(f"{axis}TP?")
        try:
            return float(response)
        except (ValueError, IndexError):
            self.check_controller_error()
            raise NewportESP302Error(
                f"Could not parse position from response: '{response}'"
            )

    def move_absolute(self, axis: int, position: float, wait: bool = True):
        position = position
        self._send_and_read(f"{axis}PA{position}")
        self.check_controller_error()
        if wait:
            self.wait_for_motion_to_stop(axis)

    def is_motion_done(self, axis: int) -> bool:
        response = self._send_and_read(f"{axis}MD?")
        return response == "1"

    def wait_for_motion_to_stop(self, axis: int, timeout_sec=60):
        self.logger(f"Waiting for motion on axis {axis} to complete...", "INFO")
        start_time = time.time()
        while True:
            if self.is_motion_done(axis):
                self.logger(f"Motion on axis {axis} completed.", "INFO")
                self.check_controller_error()
                break
            if (time.time() - start_time) > timeout_sec:
                self.stop_motion(axis)
                raise NewportESP302Error(
                    f"Timeout waiting for motion to stop on axis {axis}."
                )
            time.sleep(0.2)

    def stop_motion(self, axis: int):
        self._send_and_read(f"{axis}ST")
        self.check_controller_error()

    def motor_on(self, axis: int):
        self.logger(f"Turning motor ON for axis {axis}.", "INFO")
        self._send_and_read(f"{axis}MO")
        self.check_controller_error()

    def home_axis(self, axis: int, wait: bool = True):
        self.logger(f"Homing axis {axis}...", "INFO")
        self._send_and_read(f"{axis}OR")
        self.check_controller_error()
        if wait:
            self.wait_for_motion_to_stop(axis, timeout_sec=1000)


# --- Main Stage Class ---


@log_initialization
class NewportStage(StageBase, SerialDevice, IntegratedDevice):
    """
    Newport ESP302 Stage Class.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the Newport ESP302 Stage."""
        super().__init__(microscope_name, device_connection, configuration, device_id)

        self.stage = device_connection
        if self.stage is None:
            logger.error("The Newport ESP302 stage connection object is missing.")
            raise UserWarning("The Newport ESP302 stage connection object is missing.")

        device_config = configuration["configuration"]["microscopes"][microscope_name][
            "stage"
        ]["hardware"][device_id]

        try:
            # Ensure axis numbers are integers, not strings from YAML
            axis_numbers = [int(ax) for ax in device_config["axes_mapping"]]
            self.axes_mapping = dict(zip(device_config["axes"], axis_numbers))
        except (ValueError, TypeError) as e:
            msg = f"axes_mapping in YAML must be a list of integers. Got: {device_config['axes_mapping']}. Error: {e}"
            logger.error(msg)
            raise UserWarning(msg)

        # --- INITIALIZATION SEQUENCE ---
        logger.info("Running initialization sequence for Newport ESP302...")
        try:
            for axis_name, axis_num in self.axes_mapping.items():
                logger.info(f"Initializing axis: {axis_name} (HW: {axis_num})")
                self.stage.home_axis(axis=axis_num, wait=True)
                self.stage.motor_on(axis=axis_num)
            logger.info("Initialization sequence complete.")
        except NewportESP302Error as e:
            logger.error(f"Failed to initialize Newport stage: {e}")
            raise UserWarning(f"Failed to initialize Newport stage: {e}")

        for axis_name in self.axes:
            setattr(self, f"{axis_name}_pos", 0.0)

        self.report_position()

    def __del__(self) -> None:
        """Delete the Newport Stage connection."""
        try:
            if self.stage is not None:
                self.stage.disconnect()
                logger.debug("Newport ESP302 stage connection closed.")
        except (AttributeError, BaseException) as e:
            logger.error(f"Newport Stage Exception during __del__: {e}")

    @classmethod
    def connect(cls, port: str, baudrate: int, timeout: float) -> NewportESP302API:
        """
        Connect to the NewportStage.
        NOTE: For this Telnet device, parameters are re-purposed to match the framework:
        - `port` from YAML is the HOST IP ADDRESS (string).
        - `baudrate` from YAML is the NETWORK PORT (integer).
        - `timeout` from YAML is the connection timeout.
        """
        try:
            host_ip = port
            network_port = baudrate
            newport_api = NewportESP302API(
                host_ip, network_port, timeout, logger_func=logger.info
            )
            newport_api.connect()
            return newport_api
        except NewportESP302Error as e:
            logger.error(f"Communication Error: {e}")
            raise UserWarning(
                f"Could not communicate with Newport ESP302 at {host_ip}:{network_port}: {e}"
            )

    def report_position(self) -> dict:
        """Reports the position for all configured axes."""
        position = {}
        try:
            for axis_name, axis_num in self.axes_mapping.items():
                current_pos = self.stage.get_position(axis=axis_num)
                setattr(self, f"{axis_name}_pos", current_pos)
            position = self.get_position_dict()
            logger.debug(f"Newport ESP302 - Position: {position}")
        except NewportESP302Error as e:
            logger.error(f"Communication Error during report_position: {e}")
            position = self.get_position_dict()
        return position

    def move_axis_absolute(
        self, axis: str, abs_pos: float, wait_until_done=True
    ) -> bool:
        """Implement movement logic along a single axis."""
        if axis not in self.axes_mapping:
            logger.warning(f"Attempted to move non-existent axis '{axis}'. Ignoring.")
            return False

        move_dictionary = {f"{axis}_abs": abs_pos}
        return self.move_absolute(move_dictionary, wait_until_done)

    def move_absolute(self, move_dictionary: dict, wait_until_done=True) -> bool:
        """Move stage along one or more axes."""
        pos_dict = self.verify_abs_position(move_dictionary)
        if not pos_dict:
            return False

        try:
            for axis_name, target_pos in pos_dict.items():
                if axis_name in self.axes_mapping:
                    axis_num = self.axes_mapping[axis_name]
                    self.stage.move_absolute(
                        axis=axis_num, position=target_pos, wait=wait_until_done
                    )
            self.report_position()
        except NewportESP302Error as e:
            logger.error(f"Newport ESP302: move_absolute failed - {e}")
            self.report_position()
            return False
        return True

    def stop(self) -> None:
        """Stop all stage movement abruptly."""
        try:
            for axis_num in self.axes_mapping.values():
                self.stage.stop_motion(axis=axis_num)
        except NewportESP302Error as e:
            logger.error(f"Newport ESP302 - Stage stop failed: {e}")
