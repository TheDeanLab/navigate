# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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


#  Standard Library Imports
import logging
from typing import Any, Dict

# Third Party Imports

# Local Imports
from navigate.model.devices.remote_focus.base import RemoteFocusBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASIRemoteFocus(RemoteFocusBase , SerialDevice):
    """ASIRemoteFocus Class - Analog control of the remote focus device."""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        *args,
        **kwargs,
    ) -> None:
        """Initialize the ASIRemoteFocus class.

        Parameters
        ----------
        microscope_name : str
            The microscope name.
        device_connection : Any
            The device connection object.
        configuration : Dict[str, Any]
            The configuration dictionary.

        """

        super().__init__(microscope_name, device_connection, configuration)

        #: Any: Device connection object.
        self.remote_focus = device_connection

        #: str: Output axis on Tiger Controller
        self.axis = self.device_config["hardware"]["axis"]

    @classmethod
    def connect(cls, port, baudrate=115200, timeout=0.25):
        """Build ASILaser Serial Port connection

        Parameters
        ----------
        port : str
            Port for communicating with the filter wheel, e.g., COM1.
        baudrate : int
            Baud rate for communicating with the filter wheel, default is 115200.
        timeout : float
            Timeout for communicating with the filter wheel, default is 0.25.

        Returns
        -------
        tiger_controller : TigerController
            ASI Tiger Controller object.
        """
        # wait until ASI device is ready
        tiger_controller = TigerController(port, baudrate)
        tiger_controller.connect_to_serial()
        if not tiger_controller.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")
        return tiger_controller

    def adjust(self, exposure_times, sweep_times, offset=None):
        """Adjust the waveform.

        This method adjusts the waveform parameters.
        Based on the sensor mode and readout direction, either the triangle or ramp function will be called. 

        Parameters
        ----------
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel
        offset : float, optional
            Offset value for the remote focus waveform, by default None
        """

        # to determine if the waveform has to be triangular
        sensor_mode = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["sensor_mode"]
        readout_direction = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["readout_direction"]

        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        waveform_constants = self.configuration["waveform_constants"]
        imaging_mode = microscope_state["microscope_name"]
        zoom = microscope_state["zoom"]

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.
                # Should Assert.
                laser = channel["laser"]
                exposure_time = exposure_times[channel_key]
                self.sweep_time = sweep_times[channel_key]

                # Remote Focus Parameters
                # Validation for when user puts a '-' or '.' in spinbox
                temp = waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                    laser
                ]["amplitude"]
                if temp == "-" or temp == ".":
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["amplitude"] = "1000"
                
                amplitude = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["amplitude"]
                )

                # Validation for when user puts a '-' in spinbox
                temp = waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                    laser
                ]["offset"]
                if temp == "-" or temp == ".":
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["offset"] = "0"

                remote_focus_offset = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["offset"]
                )
                if offset is not None:
                    remote_focus_offset += offset    

                # Calculate the Waveforms
                if sensor_mode == "Light-Sheet" and (
                    readout_direction == "Bidirectional"
                    or readout_direction == "Rev. Bidirectional"
                ):
                    sweep_time=self.sweep_time
                    amplitude = amplitude
                    offset = remote_focus_offset
                
                    self.triangle(sweep_time, amplitude, offset)

                else:
                    self.ramp(exposure_time, amplitude, remote_focus_offset)
    
    def triangle(
        self,
        sweep_time=0.24,
        amplitude=1,
        offset=0,
    ):
        """Sends the tiger controller commands to initiate the triangle wave.
        
        The waveform starts at the offset and immediately rises linearly to 2x amplitude 
        (amplitude here refers to 1/2 peak-to-peak) and immediately falls linearly back
        to the offset. The waveform is a periodic waveform with no delay periods between
        cycles.

        Parameters
        ----------
        sweep_time : Float
            Unit - Seconds
        amplitude : Float
            Unit - Volts
        offset : Float
            Unit - Volts
        """

        # Converts sweep_time to ms and amplitude and offset to mV
        period = int(round(sweep_time * 1000)) 
        amplitude *= 1000
        offset *= 1000

        # Triangle waveform
        self.remote_focus.SA_waveform(self.axis, 1, amplitude, offset, period)
        # Waveform is free running after it is triggered 
        self.remote_focus.SAM(self.axis, 4)

    def ramp(
        self,
        exposure_time=0.2,
        amplitude=1,
        offset=0.5,
    ):
        """Sends the tiger controller commands to initiate the ramp wave.

        The waveform starts at offset and immediately rises linearly to 2x amplitude 
        (amplitude here refers to 1/2 peak-to-peak) and then immediately drops back 
        down to the offset voltage during the fall period. 

        There is a delay period after each cycle that comes from the PLC, which is 
        not included in this function. 

        Parameters
        ----------
        exposure_time : Float
            Unit - Seconds
        sweep_time : Float
            Unit - Seconds
        remote_focus_delay : Float
            Unit - seconds
        camera_delay : Float
            Unit - seconds
        fall : Float
            Unit - seconds
        amplitude : Float
            Unit - Volts
        offset : Float
            Unit - Volts
        """

        # Converts exposure_time to ms and amplitude and offset to mV
        amplitude *= 1000
        offset *= 1000
        exposure_time = int(round(exposure_time * 1000))

        # Ramp waveform that is triggered on TTL inputs
        self.remote_focus.SA_waveform(self.axis, 128, amplitude, offset, exposure_time)
        # The waveform cycles once and waits for another TTL inputs
        self.remote_focus.SAM(self.axis, 2)
    
    def move(self, exposure_times, sweep_times, offset=None):
        """Move the remote focus.

        This method moves the remote focus.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel
        offset : float
            The offset of the signal in volts.
        """
        
        self.adjust(exposure_times, sweep_times, offset)
    
    def turn_off(self): 
        """Stops the remote focus waveform"""
        self.remote_focus.SAM(self.axis, 0)

    def close(self):
        """Close the ASI remote_focus serial port.

        Stops the remote focus waveform and then closes the port.
        """
        if self.remote_focus.is_open():
            self.turn_off()
            logger.debug("ASI Remote Focus - Closing Device.")
            self.remote_focus.disconnect_from_serial()

    def __del__(self):
        """Destructor for the ASIRemoteFocus class."""
        self.close()

        
