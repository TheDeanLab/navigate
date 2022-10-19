# serialport.py
from serial import Serial
from serial import SerialException
from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial.tools import list_ports
 
class TigerController:
    """
    A utility class for managing a RS232 serial connection using the pyserial library.
 
    """
 
    def __init__(self, com_port: str, baud_rate: int, verbose: bool = True):
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
 
    def connect_to_serial(self, rx_size: int = 12800, tx_size: int = 12800, read_timeout: int = 1, write_timeout: int = 1) -> None:
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
            self.print(f"SerialException: can't connect to {self.com_port} at {self.baud_rate}!")
 
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
        return response # in case we want to read the response