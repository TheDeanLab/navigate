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
#

#  Standard Library Imports
import logging
from typing import Any, Dict


# Local Imports
from navigate.model.devices.galvo.base import GalvoBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASIGalvo(GalvoBase, SerialDevice):
    """GalvoASI Class - ASI DAQ Control of Galvanometers"""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the GalvoASI class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            Connection to the NI DAQ device.
        configuration : Dict[str, Any]
            Dictionary of configuration parameters.
        device_id : int
            Galvo ID. Default is 0.
        """
        super().__init__(microscope_name, device_connection, configuration, device_id)

        #: Any: Device connection.
        self.galvo = device_connection

        #: dict: Dictionary of microscope configuration parameters.
        self.configuration = configuration

        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: int: Galvo ID.
        self.galvo_id = device_id

        #: str: Galvo Axis
        self.axis = self.device_config["hardware"]["axis"]  # .get("axis","B")
        logger.debug(f"galvo axis: {self.axis}")

    def __str__(self) -> str:
        """Return string representation of the GalvoASI."""
        return "GalvoASI"

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

    def adjust(self, exposure_times, sweep_times):
        """Adjust the galvo waveform to account for the camera readout time.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of camera exposure time in seconds on a per-channel basis.
            e.g., exposure_times = {"channel_1": 0.1, "channel_2": 0.2}
        sweep_times : dict
            Dictionary of acquisition sweep time in seconds on a per-channel basis.
            e.g., sweep_times = {"channel_1": 0.1, "channel_2": 0.2}

        Returns
        -------
        waveform_dict : dict
            Dictionary that includes the galvo waveforms on a per-channel basis.
        """

        # TODO: variables galvo_amplitude, offset, etc., are local in the parent
        #  method and not assigned as an attribute. As such, much of this code is
        #  duplicated. We could consider refactoring this to avoid duplication.

        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        microscope_name = microscope_state["microscope_name"]
        zoom_value = microscope_state["zoom"]
        galvo_factor = self.configuration["waveform_constants"]["other_constants"].get(
            "galvo_factor", "none"
        )
        galvo_parameters = self.configuration["waveform_constants"]["galvo_constants"][
            self.galvo_name
        ][microscope_name][zoom_value]
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["sample_rate"]

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.
                # Should Assert.
                exposure_time = exposure_times[channel_key]
                self.sweep_time = sweep_times[channel_key]

                # galvo Parameters
                try:
                    galvo_amplitude = float(galvo_parameters.get("amplitude", 0))
                    galvo_offset = float(galvo_parameters.get("offset", 0))
                    galvo_rising_ramp = float(galvo_parameters.get("rising_ramp", 50))
                    if float(galvo_parameters.get("frequency", 10)) == 0:
                        galvo_period = exposure_time
                    else:
                        galvo_period = exposure_time / float(
                            galvo_parameters.get("frequency", 10)
                        )
                    factor_name = None
                    if galvo_factor == "channel":
                        factor_name = (
                            f"Channel {channel_key[channel_key.index('_')+1:]}"
                        )
                    elif galvo_factor == "laser":
                        factor_name = channel["laser"]
                    if factor_name and factor_name in galvo_parameters.keys():
                        galvo_amplitude = float(
                            galvo_parameters[factor_name].get("amplitude", 0)
                        )
                        galvo_offset = float(
                            galvo_parameters[factor_name].get("offset", 0)
                        )

                except ValueError as e:
                    logger.debug(
                        f"{e} waveform constants.yml doesn't have parameter "
                        f"amplitude/offset/frequency for {self.galvo_name}"
                    )
                    return

                # Calculate the Waveforms
                if self.galvo_waveform == "sawtooth":
                    period = galvo_period
                    amplitude = galvo_amplitude
                    offset = galvo_offset
                    duty_cycle = galvo_rising_ramp

                    # Duty cycle must be either 0, 50, or 100
                    # If the duty cycle is not 0, 50, or 100, it will round to the nearest value
                    if duty_cycle not in (0, 50, 100):
                        temp = duty_cycle
                        remainder = duty_cycle % 100
                        if remainder < 25:
                            duty_cycle = temp - remainder
                        elif remainder < 75:
                            duty_cycle = temp - remainder + 50
                        else:
                            duty_cycle = 100
                        logger.debug(
                            f"Invalid duty cycle given. Duty cycle value corrected to {duty_cycle}"
                        )
                    self.configuration["waveform_constants"]["galvo_constants"][
                        self.galvo_name
                    ][microscope_name][zoom_value]["rising ramp"] = duty_cycle
                    print(
                        self.configuration["waveform_constants"]["galvo_constants"][
                            self.galvo_name
                        ][microscope_name][zoom_value]["rising ramp"]
                    )
                    self.sawtooth(period, amplitude, offset, duty_cycle)

                elif self.galvo_waveform == "sine":
                    period = galvo_period
                    amplitude = galvo_amplitude
                    offset = galvo_offset

                    self.sine_wave(period, amplitude, offset)

                else:
                    print("Unknown Galvo waveform specified in configuration file.")
                    continue

    def sawtooth(self, period=10, amplitude=1, offset=0, duty_cycle=100):
        """
        Sends the tiger controller commands to initiate the sawtooth wave.

        If the duty cycle given is 50, a triangle wave will be initiated.

        Parameters
        ----------
        period : Float
            Unit - milliseconds
        amplitude : Float
            Unit - Volts
        offset : Float
            Unit - Volts
        duty_cycle : Float
            Unit - Percent
        """

        # Converts period to ms and amplitude and offset to mV
        period = int(round(period * 1000))
        amplitude *= 1000
        offset *= 1000

        if duty_cycle == 0:
            # Negative amplitude reverses the polarity of the waveform
            amplitude = amplitude * -1
            # Sawtooth waveform that is triggered on TTL input
            self.galvo.SA_waveform(self.axis, 128, amplitude, offset, period)

        if duty_cycle == 50:
            # Adjusts the period for a triangle waveform
            period = 2 * round(period / 2)
            # Triangle waveform that is triggered on TTL input
            self.galvo.SA_waveform(self.axis, 129, amplitude, offset, period)

        if duty_cycle == 100:
            # Sawtooth waveform that is triggered on TTL input
            self.galvo.SA_waveform(self.axis, 128, amplitude, offset, period)

        # Waveform is free running after TTL input
        self.galvo.SAM(self.axis, 4)

    def sine_wave(self, period=10.0, amplitude=1.0, offset=0.0):
        """Sends the tiger controller commands to initiate the sine wave.

        Parameters
        ----------
        period : Float
            Unit - milliseconds
        amplitude : Float
            Unit - Volts
        offset : Float
            Unit - Volts

        """

        # Converts period to ms and amplitude and offset to mV
        period = int(round(period * 1000))
        amplitude *= 1000
        offset *= 1000

        # Sine wave that is triggered on TTL input
        self.galvo.SA_waveform(self.axis, 131, amplitude, offset, period)
        # Waveform is free running after it is triggered
        self.galvo.SAM(self.axis, 4)

    def turn_off(self):
        """Stops the galvo waveform"""
        self.galvo.SAM(self.axis, 0)

    def close(self):
        """Close the ASI galvo serial port.

        Stops the remote focus waveform and then closes the port.
        """
        if self.galvo.is_open():
            self.turn_off()
            logger.debug("ASI Remote Focus - Closing Device.")
            self.galvo.disconnect_from_serial()

    def __del__(self):
        """Destructor for the ASIGalvo class."""
        self.close()
