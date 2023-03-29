# serialport.py
from serial import Serial
from serial import SerialException
from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial.tools import list_ports

import time


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
        self.print = self.report_to_console

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
            self.print(
                f"SerialException: can't connect to {self.com_port} at {self.baud_rate}!"
            )

        if self.is_open():
            # clear the rx and tx buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            # report connection status to user
            self.print("Connected to the serial port.")
            self.print(f"Serial port = {self.com_port} :: Baud rate = {self.baud_rate}")

    def disconnect_from_serial(self) -> None:
        """
        Disconnect from the serial port if it's open.
        """
        if self.is_open():
            self.serial_port.close()
            self.print("Disconnected from the serial port.")

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
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

        # send the serial command to the controller
        command = bytes(f"{cmd}\r", encoding="ascii")
        self.serial_port.write(command)
        self.print(f"Sent Command: {command.decode(encoding='ascii')}")

    def read_response(self) -> str:
        """
        Read a line from the serial response.
        """
        response = self.serial_port.readline()
        response = response.decode(encoding="ascii")

        # Remove leading and trailing empty spaces
        response = response.strip()
        self.print(f"Received Response: {response}")
        return response  # in case we want to read the response

    # Basic Serial Commands

    def moverel(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        """Move the stage with a relative move on multiple axes"""
        self.send_command(f"MOVREL X={x} Y={y} Z={z}\r")
        res = self.read_response()
        if res.startswith(":N"):
            raise TigerException(res)

    def moverel_axis(self, axis: str, distance: int) -> None:
        """Move the stage with a relative move on one axis"""
        self.send_command(f"MOVREL {axis}={distance}\r")
        res = self.read_response()
        if res.startswith(":N"):
            raise TigerException(res)

    def move(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        """Move the stage with an absolute move on multiple axes"""
        self.send_command(f"MOVE X={x} Y={y} Z={z}\r")
        res = self.read_response()
        if res.startswith(":N"):
            raise TigerException(res)

    def move_axis(self, axis: str, distance: int) -> None:
        """Move the stage with an absolute move on one axis"""
        self.send_command(f"MOVE {axis}={distance}\r")
        res = self.read_response()
        if res.startswith(":N"):
            raise TigerException(res)

    def set_max_speed(self, axis: str, speed: int) -> None:
        """Set the speed on a specific axis. Speed is in mm/s."""
        self.send_command(f"SPEED {axis}={speed}\r")
        res = self.read_response()
        if res.startswith(":N"):
            raise TigerException(res)

    def get_position(self, axis: str) -> int:
        """Return the position of the stage in ASI units (tenths of microns)."""
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)
        else:
            try:
                pos = int(response.split(" ")[1])
            except:
                pos = float('Inf')
            return pos

    def get_position_um(self, axis: str) -> float:
        """Return the position of the stage in microns."""
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)
        else:
            return float(response.split(" ")[1]) / 10.0

    # Utility Functions

    def is_axis_busy(self, axis: str) -> bool:
        """Returns True if the axis is busy."""
        self.send_command(f"RS {axis}?\r")
        res = self.read_response()
        if res.startswith(":N"):
            raise TigerException(res)
        else:
            return "B" in res

    def is_device_busy(self) -> bool:
        """Returns True if any axis is busy."""
        self.send_command("/")
        res = self.read_response()
        if res.startswith(":N"):
            raise TigerException(res)
        else:
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
            busy = self.is_device_busy()
            if waiting_time >= timeout:
                break
            waiting_time += 0.1
            time.sleep(0.1)
        self.verbose = temp

    def stop(self):
        """
        Stop all stage movement immediately
        """

        self.send_command("HALT")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)
        else:
            print("ASI Stages stopped successfully")

    def set_speed(self, **axes:float):
        """Set speed"""
        axes = " ".join([f"{x}={round(v, 6)}" for x,v in axes.items()])
        self.send_command(f"SPEED {axes}")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)
        
    def get_speed(self, axis: str):
        self.send_command(f"SPEED {axis}?")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)
        else:
            return float(response.split("=")[1])

    def get_encoder_counts_per_mm(self, axis: str):
        """
        Get encoder counts pre mm of axis
        """

        self.send_command(f"CNTS {axis}?")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)
        else:
            return float(response.split("=")[1].split()[0])
        
    def scanr(self, start_position_mm: float, end_position_mm: float, enc_divide: float=0, axis: str='X'):
        """
        Set scan range.
        """
        enc_divide_mm = self.get_encoder_counts_per_mm(axis)
        if enc_divide == 0:
            enc_divide = enc_divide_mm
        else:
            enc_divide = enc_divide * enc_divide_mm
        command = f"SCANR X={round(start_position_mm, 6)} Y={round(end_position_mm, 6)} Z={round(enc_divide)}"
        self.send_command(command)
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)
        
    def start_scan(self, axis: str, is_single_axis_scan: bool=True):
        """
        Start scan

        axis: 'X' or 'Y'
        is_single_axis_scan: True for single axis scan
        """
        fast_axis_id = 0 if axis == 'X' else 1
        slow_axis_id = 1 - fast_axis_id
        if is_single_axis_scan:
            slow_axis_id = 9
        self.send_command(f"SCAN S Y={fast_axis_id} Z={slow_axis_id}")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)

    def stop_scan(self):
        """
        Stop scan.
        """
        self.send_command("SCAN P")
        response = self.read_response()
        if response.startswith(":N"):
            raise TigerException(response)