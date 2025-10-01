# Copyright (c) 2021-2024 The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# This file has been adapted to control a Newport CONEX-CC stage
# by conforming to the host software's device architecture, using asi.py as a template.

# Standard Library Imports
import logging
import time
import re
import threading
from typing import Any, Dict

# Third Party Imports
from serial import Serial, SerialException

# Local Imports
try:
    from navigate.model.devices.stage.base import StageBase
    from navigate.model.devices.device_types import SerialDevice, IntegratedDevice
    from navigate.tools.decorators import log_initialization
except ImportError:
    # Dummy classes for standalone functionality if navigate is not available
    class StageBase:
        def __init__(self, *args, **kwargs): self.axes = ["x"]
        def get_position_dict(self): 
            return {self.axes[0]: getattr(self, f"{self.axes[0]}_pos", 0.0)}
        def verify_abs_position(self, pos_dict): return pos_dict
    class SerialDevice: pass
    class IntegratedDevice: pass
    def log_initialization(func): return func

# Logger Setup
p = __name__.split(".")[-1]
logger = logging.getLogger(p)


# --- CONEX-CC Specific API Logic ---

class ConexCCError(Exception):
    """Custom exception for CONEX-CC device errors."""
    pass

class ConexCCAPI:
    """
    Handles low-level serial communication with the CONEX-CC controller.
    This is the core device interface, analogous to TigerController in asi.py.
    """
    def __init__(self, port, logger_func=logging.info):
        self.port = port
        self.logger = logger_func
        self.ser = None
        self.comm_lock = threading.Lock()
        self.CONTROLLER_ADDRESS = 1
        self.STATE_MAP = {
            '0A': 'NOT REFERENCED', '0B': 'NOT REFERENCED', '0C': 'NOT REFERENCED',
            '0D': 'NOT REFERENCED', '0E': 'NOT REFERENCED', '0F': 'NOT REFERENCED',
            '10': 'NOT REFERENCED', '14': 'CONFIG', '1E': 'HOMING',
            '28': 'MOVING', '32': 'READY', '33': 'READY', '34': 'READY',
            '3C': 'DISABLE', '3D': 'DISABLE'
        }

    def connect(self):
        if self.ser and self.ser.is_open:
            self.logger("Already connected.", "DEBUG")
            return True
        try:
            self.ser = Serial(
                port=self.port, baudrate=921600, bytesize=8,
                parity='N', stopbits=1, xonxoff=True, timeout=1.0
            )
            self.logger(f"Serial port {self.port} opened.", "INFO")
            version = self.get_version()
            if version:
                self.logger(f"CONEX-CC Connected. Version: {version}", "INFO")
                return True
            else:
                self.disconnect()
                raise ConexCCError("Failed to verify version from controller.")
        except SerialException as e:
            self.ser = None
            if "PermissionError" in str(e):
                 raise ConexCCError(f"Failed to connect to {self.port}: {e}. Port may be in use.")
            raise ConexCCError(f"Failed to connect to {self.port}: {e}")


    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.logger("Disconnected from CONEX-CC.", "INFO")
        self.ser = None

    def initialize_controller(self):
        self.logger("Initializing controller with physical homing...", "INFO")
        status = self.get_status()
        state_code = status.get("raw_state_code")
        if state_code and "NOT REFERENCED" in self.STATE_MAP.get(state_code, ""):
            self.query("HT0") # Use mechanical zero switch
            self.query("OR") # Start homing
            self.logger("Physical homing sequence started. Stage will move.", "INFO")
            start_time = time.time()
            while True:
                status = self.get_status()
                if status.get("raw_state_code") in ['32', '33', '34']:
                    self.logger("Homing complete. Controller is READY.", "INFO")
                    break
                if (time.time() - start_time) > 60:
                    raise ConexCCError("Timeout waiting for controller to become READY after homing.")
                time.sleep(0.5)
        else:
            self.logger("Controller already initialized. Skipping homing.", "INFO")

    def query(self, command):
        with self.comm_lock:
            if not (self.ser and self.ser.is_open):
                raise ConexCCError("Not connected.")
            try:
                self.ser.reset_input_buffer()
                full_command = f"{self.CONTROLLER_ADDRESS}{command}\r\n".encode('ascii')
                self.logger(f"CMD > {command}", "DEBUG")
                self.ser.write(full_command)
                response = self.ser.readline().decode('ascii').strip()
                self.logger(f"RSP < {response}", "DEBUG")
                return response
            except SerialException as e:
                self.disconnect()
                raise ConexCCError(f"Serial communication error: {e}")

    def get_version(self):
        response = self.query("VE?")
        return response.replace(f"{self.CONTROLLER_ADDRESS}VE", "").strip()

    def get_position(self) -> float:
        response = self.query("TP?")
        try:
            pos_str = response.replace(f"{self.CONTROLLER_ADDRESS}TP", "").strip()
            return float(pos_str)
        except (ValueError, IndexError):
            raise ConexCCError(f"Could not parse position: '{response}'")

    def get_status(self) -> dict:
        ts_resp = self.query("TS?")
        if ts_resp:
            match = re.search(r'TS(.{4})(.{2})', ts_resp)
            if match:
                error_code, state_code = match.groups()
                state_desc = self.STATE_MAP.get(state_code, f"Unknown({state_code})")
                full_state = f"{state_desc} (Err: {error_code})"
                return {"state": full_state, "raw_state_code": state_code}
        return {"state": "Unknown", "raw_state_code": None}

    def is_motion_done(self) -> bool:
        status = self.get_status()
        state_code = status.get("raw_state_code")
        return state_code in ['32', '33', '34', '3C', '3D']

    def wait_for_motion_to_stop(self, timeout_sec=60):
        self.logger("Waiting for motion to complete...", "INFO")
        start_time = time.time()
        while True:
            if self.is_motion_done():
                self.logger("Motion completed.", "INFO")
                break
            if (time.time() - start_time) > timeout_sec:
                self.stop_motion()
                raise ConexCCError("Timeout waiting for motion to stop.")
            time.sleep(0.2)
        
    def move_absolute(self, position: float, wait=True):
        self.query(f"PA{position}")
        if wait: self.wait_for_motion_to_stop()

    def stop_motion(self):
        self.query("ST")


# --- Main Stage Class ---

@log_initialization
class ConexStage(StageBase, SerialDevice, IntegratedDevice):
    """
    CONEX-CC Stage Class.
    This class controls a single-axis Newport CONEX-CC stage via Serial.
    """
    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the CONEX-CC Stage."""
        super().__init__(microscope_name, device_connection, configuration, device_id)
        
        self.stage = device_connection
        if self.stage is None:
            logger.error("The CONEX-CC stage connection object is missing.")
            raise UserWarning("The CONEX-CC stage connection object is missing.")
        
        # Read device-specific settings from the configuration
        device_config = configuration["configuration"]["microscopes"][microscope_name]["stage"]["hardware"][device_id]

        # This is a single-axis stage
        self.axis_name = device_config["axes"][0]
        hardware_axis_name = device_config["axes_mapping"][0]
        self.axes_mapping = {self.axis_name: hardware_axis_name}
        
        setattr(self, f"{self.axis_name}_pos", 0.0)
        
        # Perform initial position report
        self.report_position()

    def __del__(self) -> None:
        """Delete the CONEX-CC Stage connection."""
        try:
            if self.stage is not None:
                self.stage.disconnect()
                logger.debug("CONEX-CC stage connection closed.")
        except (AttributeError, BaseException) as e:
            logger.error(f"CONEX-CC Stage Exception during __del__: {e}")

    @classmethod
    def connect(cls, port: str = "COM4", baud_rate: int = 921600, timeout: float = 1.0) -> ConexCCAPI:
        """Connect to the ConexCCStage."""
        try:
            # Note: baud_rate and timeout are fixed for the CONEX-CC
            conex_api = ConexCCAPI(port, logger_func=logger.info)
            conex_api.connect()
            conex_api.initialize_controller() # Perform homing on connect
            return conex_api
        except ConexCCError as e:
            logger.error(f"Communication Error: {e}")
            if "PermissionError" in str(e):
                new_message = (
                    f"Could not open COM port {port} due to a Permission Error. "
                    f"This usually means another program is holding the port open. "
                    f"Please ensure all other applications using {port} are closed."
                )
                raise UserWarning(new_message)
            raise UserWarning(f"Could not communicate with CONEX-CC via port {port}: {e}")

    def report_position(self) -> dict:
        """Reports the position for the axis and converts it to microns."""
        position = {}
        try:
            # API returns position in mm, convert to microns for the software
            current_pos_mm = self.stage.get_position()
            current_pos_microns = current_pos_mm * 1000
            setattr(self, f"{self.axis_name}_pos", current_pos_microns)
            position = self.get_position_dict()
            logger.debug(f"CONEX-CC - Position: {position} microns")
        except ConexCCError as e:
            logger.error(f"Communication Error during report_position: {e}")
        return position

    def move_axis_absolute(self, axis: str, abs_pos: float, wait_until_done=True) -> bool:
        """Implement movement logic along the single axis."""
        if axis != self.axis_name:
            logger.warning(f"Attempted to move non-existent axis '{axis}'. Ignoring.")
            return False
        
        move_dictionary = {f"{axis}_abs": abs_pos}
        return self.move_absolute(move_dictionary, wait_until_done)

    def move_absolute(self, move_dictionary: dict, wait_until_done=True) -> bool:
        """Move stage along its single axis."""
        pos_dict = self.verify_abs_position(move_dictionary)
        if not pos_dict:
            return False

        target_pos_microns = pos_dict.get(self.axis_name)
        if target_pos_microns is None:
            logger.debug("No target position found for the stage's axis in move command.")
            return True

        # Convert incoming microns to millimeters for the controller
        target_pos_mm = target_pos_microns / 1000.0
        
        try:
            self.stage.move_absolute(position=target_pos_mm, wait=wait_until_done)
            # After a successful move, update the internal position cache
            self.report_position()
        except ConexCCError as e:
            logger.error(f"CONEX-CC: move_absolute failed - {e}")
            self.report_position() # Update internal state after failure
            return False
        return True

    def stop(self) -> None:
        """Stop all stage movement abruptly."""
        try:
            self.stage.stop_motion()
        except ConexCCError as e:
            logger.error(f"CONEX-CC - Stage stop failed: {e}")

