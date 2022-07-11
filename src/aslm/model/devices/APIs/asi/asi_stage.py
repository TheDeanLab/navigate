import serial
from enum import IntEnum


class ASIStageScanMode(IntEnum):
    """
    0 for raster, 1 for serpentine
    """

    RASTER = 0
    SERPENTINE = 1


class ASIStageException(Exception):
    pass


class ASIStage:
    """
    ASIStage

    Parameters
    ----------
    com_port : str

    """

    def __init__(self, com_port: str = None):
        self.com_port = com_port if com_port else "COM6"

        self.serial_connection = serial.Serial()
        self.serial_connection.port = self.com_port
        self.serial_connection.baudrate = 9600
        self.serial_connection.parity = serial.PARITY_NONE
        self.serial_connection.bytesize = serial.EIGHTBITS
        self.serial_connection.stopbits = serial.STOPBITS_ONE
        self.serial_connection.xonoff = False
        self.serial_connection.rtscts = False
        self.serial_connection.dsrdtr = False
        self.serial_connection.write_timeout = 1
        self.serial_connection.timeout = 1

        self.serial_connection.set_buffer_size(12800, 12800)
        self.serial_connection.open()

        if self.serial_connection.is_open:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

        print(self.serial_connection.name)

    def __del__(self):
        self.serial_connection.close()

    def _send_message(self, message: str):
        """Send message over serial connection.

        Parameters
        ----------
        message : str

        """
        self.serial_connection.write(bytes(f"{message}\r", encoding="ascii"))

    def _read_response(self) -> str:
        """Receive and read the response from serial communication.

        Returns
        -------
        str

        """
        return self.serial_connection.readline().decode(encoding="ascii")

    def set_speed(self, speed):
        """Set speed of the stage.

        Parameters
        ----------
        speed

        """
        message = f"SPEED x={speed}"
        print("set speed to scan: " + message)
        self._send_message(message)
        print(self._read_response())

    def set_default_speed(self):
        """Set the default speed as the stage speed.
        Currently default values are x=10 y=10.
        """
        message = "SPEED x=10 y=10"
        print("set speed to scan: " + message)
        self._send_message(message)
        print(self._read_response())

    def set_backlash(self):
        """Set backlash on the stage."""
        message = "BACKLASH x=0.04 y=0.0"
        print("set backlash: " + message)
        self._send_message(message)
        print(self._read_response())

    def set_scan_mode(self, mode: ASIStageScanMode = ASIStageScanMode.RASTER):
        """Method to set scan mode.

        Parameters
        ----------
        mode : ASIStageScanMode

        """
        message = f"SCAN f={int(mode)}"
        self._send_message(message)
        print(self._read_response())

    def zero(self):
        """Set current position to zero."""
        message = "ZERO\r"
        self._send_message(message)
        print(self._read_response())

    def start_scan(self):
        """Start the stage scan"""
        message = "SCAN\r"
        self._send_message(message)
        print(self._read_response())

    def scanr(self, x=0, y=0):
        """Set scan raster scan start and stop.

        Parameters
        ----------
        x
        y

        """
        message = f"SCANR x={x} y={y}"
        self._send_message(message)
        print(self._read_response())

    def scanv(self, x=0, y=0, f=1.0):
        """Set vertical scan.

        Parameters
        ----------
        x
        y
        f

        Returns
        -------

        """
        message = f"SCANV x={x} y={y} f={f}"
        self._send_message(message)
        print(self._read_response())

    def info(self, axis_letter):
        """Method to fetch various information on stage axes.

        Parameters
        ----------
        axis_letter : str
            Single letter, can be 'X' or 'Y' with XY stage.

        """
        message = f"INFO {axis_letter}"
        self._send_message(message)

        # Read and parse the response in the specific required way
        lines = self.serial_connection.readlines()[1].split(
            bytes('\r', encoding="ascii")
        )
        response = "\n".join([line.decode() for line in lines])
        print(response)