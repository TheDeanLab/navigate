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
import pytest
from serial import Serial
from unittest.mock import MagicMock, patch

# Third Party Imports

# Local Imports
from navigate.model.devices.pump.tecan_x_calibur import TecanXCaliburPump

class FakeSerial:
    def __init__(self, port, baudrate, timeout):
        self.commands = []           # Record of all sent commands (as bytes).
        self.is_open = True          # Pretend the serial port is open.
        self.last_command = None     # Stores the last command sent (as string, no \r).
        self.command_responses = {}  # Maps command strings (e.g., "S5") to fake byte responses.

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def write(self, data: bytes):
        """
        Simulate sending a command to the pump.

        - Updates last_command with the stripped string version (used for read lookup).
        - Appends the raw byte-formatted command to the commands list to keep track of which order the commands are sent.
        """
        
        self.last_command = data.decode("ascii").strip()
        self.commands.append(data)

    def read(self, n: int) -> bytes:
        """ 
        Simulate receiving a response from the pump.

        If a response has been predefined for the last command (e.g., to simulate an error or custom reply),
        that specific response is returned.

        Otherwise, a default success response (b"/00") is returned to simulate normal operation.
        """
        if self.last_command in self.command_responses:
            return self.command_responses[self.last_command]
        return b"/00" # If no command has been sent yet, return the "success" response as fallback.

@pytest.fixture
def fake_pump():
    """
    Fixture that returns a TecanXCaliburPump with a mocked serial connection.
    """

    # Pick some speeds within the known bounds 0-40.
    min_speed_code = 2
    max_speed_code = 19
    port = "FAKE"
    baudrate = 9600
    timeout = 0.5

    pump = TecanXCaliburPump(
        device_name="TestPump",
        port=port,               
        baudrate=baudrate,
        timeout=timeout,
        min_speed_code=min_speed_code, 
        max_speed_code=max_speed_code,
    )
    
    pump.serial = FakeSerial(port, baudrate, timeout)
    
    return pump

def test_set_speed_command_rejected(fake_pump):
    """
    Simulate a firmware-level rejection of a valid speed code.

    This test configures the FakeSerial to return error code '/03' (Invalid Operand)
    in response to a speed code that is within the allowed local range. This models a case
    where the driver sends a syntactically valid command (e.g., 'S4'), but the pump 
    firmware rejects the operand value due to internal state or configuration.

    The test verifies that the driver:
    - Sends the command correctly.
    - Parses the response.
    - Raises a RuntimeError with an appropriate error message.
    """
    valid_speed = fake_pump.max_speed_code - 1 # Within bounds.

    fake_pump.serial.command_responses["S" + str(valid_speed)] = b"/03" # Simulate command-response.

    # Make sure the pre-defined response raises the correct error.
    with pytest.raises(RuntimeError, match="Pump error /3: Invalid operand - bad parameter value"):
        fake_pump.set_speed(valid_speed) 

@patch("serial.Serial")
def test_connect_success(mock_serial_class): # Argument passed automatically from patch (mocked version of Serial).
    """
    Simulate a successful connection using FakeSerial via patching.
    """
    # Create a custom FakeSerial instance to return instead of MagicMock.
    fake_serial = FakeSerial(port="FAKE", baudrate=9600, timeout=0.5)
    fake_serial.command_responses["ZR"] = b"/00"  # Simulate valid response.

    # Make sure Serial() returns this custom fake.
    mock_serial_class.return_value = fake_serial

    # Create the pump and call connect — now it will receive the FakeSerial.
    pump = TecanXCaliburPump("TestPump", port="FAKE")
    pump.connect()

    # Assertions
    assert pump.serial == fake_serial
    assert fake_serial.commands[-1] == b"ZR\r"
    assert fake_serial.is_open

@patch("serial.Serial")
def test_connect_initialization_error(mock_serial_class): # Argument passed automatically from patch (mocked version of Serial).
    """
    Simulate a pump that fails to initialize (command 'ZR', response '/01').

    Verifies that:
    - The 'ZR' command is sent.
    - The driver raises RuntimeError when pump reports an init failure.
    """
    # Create a custom FakeSerial instance to return instead of MagicMock.
    fake_serial = FakeSerial(port="FAKE", baudrate=9600, timeout=0.5)
    fake_serial.command_responses["ZR"] = b"/01"  # Simulate "fail" response.

    # Make sure Serial() returns this custom fake.
    mock_serial_class.return_value = fake_serial

    # Create the pump.
    pump = TecanXCaliburPump("TestPump", port="FAKE")

    # Expect a RuntimeError due to /01 response.
    with pytest.raises(RuntimeError, match="Pump error /1: Initialization error"):
        pump.connect()

    # Check that the correct command was sent.
    assert pump.serial.commands[-1] == b"ZR\r"

@patch("serial.Serial")
def test_connect_raises_if_serial_open_fails(mock_serial_class):
    """
    Simulates a failure during Serial.open() to verify that the TecanXCaliburPump.connect() 
    method does not suppress the exception. Instead, it should propagate the IOError 
    indicating that the serial port could not be opened.
    """
    fake = FakeSerial(port="FAKE", baudrate=9600, timeout=0.5)

    # Function that raises error when called. This is used to simulate a failed Serial.open().
    def raise_open(): raise IOError("Port failed")
    
    fake.open = raise_open # Override open() in FakeSerial.

    # Instructs mock class to return our custom FakeSerial instance instead of MagicMock.
    mock_serial_class.return_value = fake 
    
    pump = TecanXCaliburPump("TestPump", port="FAKE")

    # If error from open() is passed correctly the connect should fail.
    with pytest.raises(IOError, match="Port failed"):
        pump.connect()

def test_send_command_raises_if_serial_is_none():
    """
    Verifies that send_command() raises if self.serial is None.
    """
    pump = TecanXCaliburPump("TestPump", port="FAKE")
    pump.serial = None  # Simulate uninitialized or failed connection

    with pytest.raises(RuntimeError, match="Serial object is None"):
        pump.send_command("ZR")

def test_move_absolute_success_standard_and_fine_modes(fake_pump):
    """
    Test that move_absolute() sends the correct command and succeeds in both
    standard and fine positioning modes, assuming valid position input.

    Verifies that:
    - The correct 'A{pos}' command is sent.
    - The pump responds with success.
    - No exception is raised.
    """
    # --- Standard mode ---
    fake_pump.fine_positioning = False
    position_std = 3000  # Max allowed position in standard (non-fine) mode.

    # Predefine the pump's response to this specific absolute move command.
    fake_pump.serial.command_responses[f"A{position_std}"] = b"/00"

    # Send the move_absolute command (which internally sends 'A{position}' + parses response).
    fake_pump.move_absolute(position_std)

    # Verify that the correct byte-encoded command was sent to the serial interface.
    assert fake_pump.serial.commands[-1] == f"A{position_std}\r".encode()

    # --- Fine positioning mode ---
    fake_pump.fine_positioning = True
    position_fine = 24000  # Max allowed position in fine mode.
    fake_pump.serial.command_responses[f"A{position_fine}"] = b"/00"

    fake_pump.move_absolute(position_fine)
    assert fake_pump.serial.commands[-1] == f"A{position_fine}\r".encode()

def test_move_absolute_out_of_bounds_raises(fake_pump):
    """
    Verify that move_absolute() raises ValueError when given a position
    outside the valid range for the current positioning mode.
    """
    # Standard mode: max is 3000.
    fake_pump.fine_positioning = False
    with pytest.raises(ValueError, match="out of bounds"):
        fake_pump.move_absolute(3000 + 1)

    # Fine mode: max is 24000.
    fake_pump.fine_positioning = True
    with pytest.raises(ValueError, match="out of bounds"):
        fake_pump.move_absolute(24000 + 1)

def test_set_fine_positioning_mode_toggle(fake_pump):
    """
    Verify that set_fine_positioning_mode() sends the correct 'N' and 'R' commands,
    handles responses properly, and updates the fine_positioning attribute.
    """

    # Mock responses for enabling fine positioning.
    # "N1" loads the fine mode into the buffer; "R" applies the change.
    # Both return "/00" to simulate success.
    fake_pump.serial.command_responses["N1"] = b"/00"
    fake_pump.serial.command_responses["R"] = b"/00"

    # Enable fine positioning mode.
    fake_pump.set_fine_positioning_mode(True)

    # Check that the internal state was updated.
    assert fake_pump.fine_positioning is True

    # Confirm that the correct commands were sent in the correct order
    # inside set_fine_positioning_mode().
    assert fake_pump.serial.commands[-2] == b"N1\r"
    assert fake_pump.serial.commands[-1] == b"R\r"

    # Now test disabling fine positioning mode.
    # "N0" loads standard mode; "R" applies it. Again, simulate success.
    fake_pump.serial.command_responses["N0"] = b"/00"
    fake_pump.serial.command_responses["R"] = b"/00"

    fake_pump.set_fine_positioning_mode(False)

    assert fake_pump.fine_positioning is False
    assert fake_pump.serial.commands[-2] == b"N0\r"
    assert fake_pump.serial.commands[-1] == b"R\r"