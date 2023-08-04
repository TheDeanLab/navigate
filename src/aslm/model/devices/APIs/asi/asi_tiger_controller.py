# serialport.py
from serial import Serial
from serial import SerialException
from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial.tools import list_ports
import threading

import time
import logging


class TigerException(Exception):
    """
    Exception raised when error code from Tiger Console is received.

    Atrributes:
        - command: error code received from Tiger Console

"""

    def __init__(self, code: str):

        self.error_codes = {
            ":N-1": "Unknown Command (Not Issued in TG-1000)",
            ":N-2": "Unrecognized Axis Parameter (valid axes are dependent on the controller)",
            ":N-3": "Missing parameters (command received requires an axis parameter such as x=1234)",
            ":N-4": "Parameter Out of Range",
            ":N-5": "Operation failed",
            ":N-6": "Undefined Error (command is incorrect, but the controller does not know exactly why.",
            ":N-7": "Invalid Card Address",
            ":N-21": "Serial Command halted by the HALT command",
        }

        self.code = code
        self.message = self.error_codes[
            code
        ]  # Gets the proper message based on error code received.
        super().__init__(
            self.message
        )  # Sends message to base exception constructor for python purposes

    def __str__(self):
        return f"{self.code} -> {self.message}"  # Overrides base Exception string to be displayed in traceback


class TigerController:
    """
    A utility class for managing a RS232 serial connection using the pyserial library.

    """

    def __init__(self, com_port: str, baud_rate: int, verbose: bool = False):
        self.serial_port = Serial()
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.verbose = verbose
        self.default_axes_sequence = None
        self.safe_to_write = threading.Event()
        self.safe_to_write.set()

    @staticmethod
    def scan_ports() -> list[str]:
        """
        Returns a sorted list of COM ports.
        """
        com_ports = [port.device for port in list_ports.comports()]
        com_ports.sort(key=lambda value: int(value[3:]))
        return com_ports

    def connect_to_serial(
        self,
        rx_size: int = 12800,
        tx_size: int = 12800,
        read_timeout: int = 1,
        write_timeout: int = 1,
    ) -> None:
        """
        Connect to the serial port.
        """
        self.serial_port.port = self.com_port
        self.serial_port.baudrate = self.baud_rate
        self.serial_port.parity = PARITY_NONE
        self.serial_port.bytesize = EIGHTBITS
        self.serial_port.stopbits = STOPBITS_ONE
        self.serial_port.xonoff = False
        self.serial_port.rtscts = False
        self.serial_port.dsrdtr = False
        self.serial_port.write_timeout = write_timeout
        self.serial_port.timeout = read_timeout

        # set the size of the rx and tx buffers before calling open
        self.serial_port.set_buffer_size(rx_size, tx_size)

        # try to open the serial port
        try:
            self.serial_port.open()
        except SerialException:
            self.report_to_console(
                f"SerialException: can't connect to {self.com_port} at {self.baud_rate}!"
            )

        if self.is_open():
            # clear the rx and tx buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            # report connection status to user
            self.report_to_console("Connected to the serial port.")
            self.report_to_console(f"Serial port = {self.com_port} :: Baud rate = {self.baud_rate}")

            # get default motor axes sequenc
            self.send_command("BU X")
            response = self.read_response()
            lines = response.split("\r")
            for line in lines:
                if line.startswith("Motor Axes:"):
                    self.default_axes_sequence = line[line.index(":")+2:].split(" ")
                    self.report_to_console("Get the default axes sequence from the ASI device successfully!")
                    break

    def disconnect_from_serial(self) -> None:
        """
        Disconnect from the serial port if it's open.
        """
        if self.is_open():
            self.serial_port.close()
            self.report_to_console("Disconnected from the serial port.")

    def is_open(self) -> bool:
        """
        Returns True if the serial port exists and is open.
        """
        # short circuits if serial port is None
        return self.serial_port and self.serial_port.is_open

    def report_to_console(self, message: str) -> None:
        """
        Print message to the output device, usually the console.
        """
        # useful if we want to output data to something other than the console (ui element etc)
        if self.verbose:
            print(message)

    def send_command(self, cmd: bytes) -> None:
        """
        Send a serial command to the device.
        """
        # always reset the buffers before a new command is sent
        self.safe_to_write.wait()
        self.safe_to_write.clear()
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

        # send the serial command to the controller
        self.report_to_console(cmd)
        command = bytes(f"{cmd}\r", encoding="ascii")
        self.serial_port.write(command)
        # print(f"Sent Command: {command.decode(encoding='ascii')}")

    def read_response(self) -> str:
        """
        Read a line from the serial response.
        """
        response = self.serial_port.readline()
        self.safe_to_write.set()

        response = response.decode(encoding="ascii")

        # Remove leading and trailing empty spaces
        self.report_to_console(f"Received Response: {response.strip()}")
        if response.startswith(":N"):
            raise TigerException(response)
        
        return response  # in case we want to read the response

    # Basic Serial Commands for the Stage

    def moverel(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        """Move the stage with a relative move on multiple axes"""
        self.send_command(f"MOVREL X={x} Y={y} Z={z}\r")
        res = self.read_response()

    def moverel_axis(self, axis: str, distance: float) -> None:
        """Move the stage with a relative move on one axis"""
        self.send_command(f"MOVREL {axis}={round(distance, 6)}\r")
        res = self.read_response()

    def move(self, pos_dict) -> None:
        """Move the stage with an absolute move on multiple axes"""
        pos_str = " ".join([f"{axis}={round(pos, 6)}" for axis, pos in pos_dict.items()])
        self.send_command(f"MOVE {pos_str}\r")
        res = self.read_response()

    def move_axis(self, axis: str, distance: float) -> None:
        """Move the stage with an absolute move on one axis"""
        self.send_command(f"MOVE {axis}={round(distance, 6)}\r")
        res = self.read_response()

    def set_max_speed(self, axis: str, speed: float) -> None:
        """Set the speed on a specific axis. Speed is in mm/s."""
        self.send_command(f"SPEED {axis}={speed}\r")
        res = self.read_response()

    def get_axis_position(self, axis: str) -> int:
        """Return the position of the stage in ASI units (tenths of microns)."""
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        # try:
        pos = float(response.split(" ")[1])
        # except:
        #     pos = float('Inf')
        return pos

    def get_axis_position_um(self, axis: str) -> float:
        """Return the position of the stage in microns."""
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        return float(response.split(" ")[1]) / 10.0
        
    def get_position(self, axes) -> dict:
        """Return current stage position in ASI units.

        If default axes sequence has gotten from the ASI device, 
        then it will ask the device all the position in one command,
        else it will ask each axis position one by one. 

        WATCH OUT! This will return the positions in the order
        of the underlying hardware no matter what order the axes
        are passed in.

        See https://asiimaging.com/docs/products/serial_commands#commandwhere_w
        
        Returns
        -------
        dictionary:
             {axis: position}
        """

        if self.default_axes_sequence:
            cmd = f"WHERE {' '.join(axes)}\r"
            self.send_command(cmd)
            response = self.read_response()

            # return response.split(" ")[1:-1]
            pos = response.split(" ")
            axes_seq = list(filter(lambda axis: axis if axis in axes else False, self.default_axes_sequence))
            return {axis: float(pos[1+i]) for i, axis in enumerate(axes_seq)}
        else:
            result = {}
            for axis in axes:
                result[axis] = self.get_axis_position(axis)
            return result


    # Utility Functions

    def is_axis_busy(self, axis: str) -> bool:
        """Returns True if the axis is busy."""
        self.send_command(f"RS {axis}?\r")
        res = self.read_response()
        return "B" in res

    def is_device_busy(self) -> bool:
        """Returns True if any axis is busy."""
        self.send_command("/")
        res = self.read_response()
        return "B" in res

    def wait_for_device(self, report: bool = False, timeout: float = 100) -> None:
        """Waits for the all motors to stop moving."""
        if not report:
            print("Waiting for device...")
        temp = self.verbose
        self.verbose = report
        busy = True
        waiting_time = 0.0
        
        while busy:
            if waiting_time >= timeout:
                break
            busy = self.is_device_busy()
            waiting_time += 0.01
            time.sleep(0.01)

        self.verbose = temp

    def stop(self):
        """
        Stop all stage movement immediately
        """

        self.send_command("HALT")
        response = self.read_response()
        print("ASI Stages stopped successfully")

    def set_speed(self, speed_dict):
        """
        Set speed
        """
        axes = " ".join([f"{x}={round(v, 6)}" for x,v in speed_dict.items()])
        self.send_command(f"SPEED {axes}")
        response = self.read_response()

    def get_speed(self, axis: str):
        """
        Get speed
        """
        self.send_command(f"SPEED {axis}?")
        response = self.read_response()
        return float(response.split("=")[1])

    def get_encoder_counts_per_mm(self, axis: str):
        """
        Get encoder counts pre mm of axis
        """

        self.send_command(f"CNTS {axis}?")
        response = self.read_response()
        return float(response.split("=")[1].split()[0])
        
    def scanr(self, start_position_mm: float, end_position_mm: float, enc_divide: float=0, axis: str='X'):
        """
        Set scan range.
        """
        print("scan r started asi tiger controller")
        print("axis =",axis)
        enc_divide_mm = self.get_encoder_counts_per_mm(axis)
        print("encoder divide = ",enc_divide)
        print("encoder divide mm = ",enc_divide_mm)
        if enc_divide == 0:
            enc_divide = enc_divide_mm
        else:
            enc_divide = enc_divide * enc_divide_mm
            print("encoder divide updated = ",enc_divide)

        command = f"SCANR X={round(start_position_mm, 6)} Y={round(end_position_mm, 6)} Z={round(enc_divide)}"
        self.send_command(command)
        response = self.read_response()
        
    def start_scan(self, axis: str, is_single_axis_scan: bool=True):
        """
        Start scan

        axis: 'X' or 'Y'
        is_single_axis_scan: True for single axis scan
        """
        print("Scan started ASI tiger controller")
        fast_axis_id = 0 if axis == 'X' else 1
        slow_axis_id = 1 - fast_axis_id
        if is_single_axis_scan:
            slow_axis_id = 9
        self.send_command(f"SCAN S Y={fast_axis_id} Z={slow_axis_id}")
        response = self.read_response()
       

    def stop_scan(self):
        """
        Stop scan.
        """
        self.send_command("SCAN P")
        response = self.read_response()

    # Basic Serial Commands for Filter Wheels

    def send_filter_wheel_command(self, cmd: bytes) -> None:
        """
        Send a serial command to the filter wheel.
        """
        # always reset the buffers before a new command is sent
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

        # send the serial command to the controller
        command = bytes(f"{cmd}\n\r", encoding="ascii")
        self.serial_port.write(command)
        self.read_response()
        # print(f"Sent Command: {command.decode(encoding='ascii')}")

    def select_filter_wheel(self, filter_wheel_number=0):
        """
        Select the filter wheel, e.g., 0, 1...

        Sets the current filter wheel for subsequent commands. Prompt shows currently selected wheel, e.g., 0> is result of FW 0 command. If the selected wheel is HOMED and ready to go, the FW command returns the selected wheel as normal. If the wheel is not ready for any reason, the response ERR is returned. Example:

        0> FW 1 1 Normal – switch to FW 1
        1> FW 0 ERR FW 0 not ready
        0> Although FW 0 not ready – can still change FW 0 parameters.
        """
        assert filter_wheel_number in range(2)
        self.send_filter_wheel_command(f"FW {filter_wheel_number}")
        response = self.read_response()

    def move_filter_wheel(self, filter_wheel_position=0):
        """
        Move to filter position n , where n is a valid filter position.
        """
        assert filter_wheel_position in range(8)
        self.send_filter_wheel_command(f"MP {filter_wheel_position}")
        response = self.read_response()

    def move_filter_wheel_to_home(self):
        """
        Causes current wheel to seek its home position.
        """
        self.send_filter_wheel_command("HO")
        response = self.read_response()

    def change_filter_wheel_speed(self, speed=0):
        """
        Selects a consistent set of preset acceleration and speed parameters.
        Supported in version 2.4 and later.

        0	Default - directly set and saved AU, AD, and VR parameters are used.
        1	Slowest and smoothest switching speed.
        2 to 8	Intermediate switching speeds.
        9	Fastest and but least reliable switching speed.
        """
        self.send_filter_wheel_command(f"SV {speed}")
        response = self.read_response()

    def halt_filter_wheel(self):
        """
        Halt filter wheel
        """
        self.send_filter_wheel_command("HA")
        response = self.read_response()
