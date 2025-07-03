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


# Standard Imports
import logging
from threading import Lock
from typing import Dict, Any

# Third Party Imports
from multiprocessing.managers import DictProxy, ListProxy

# Local Imports
from navigate.model.devices.daq.base import DAQBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASIDaq(DAQBase, SerialDevice):
    """ASIDAQ class for Data Acquisition (DAQ).

    Representation of Tiger Controller in action.
    Triggers all devices and outputs to camera trigger channel.
    """

    def __init__(
        self,
        microscope_name,
        device_connection,
        configuration: Dict[str, Any],
        device_id,
    ) -> None:
        """Initialize the ASI DAQ.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            Connection to the Tiger Controller.
        configuration : Dict[str, Any]
            Dictionary of configuration parameters.
        device_id : int
            Parameter necessary for start_device but not used here.
        """
        super().__init__(configuration)

        #: dict: Configuration dictionary.
        self.configuration = configuration

        #: dict: Camera object.
        self.camera = {}

        #: Lock: Lock for waiting to run.
        self.wait_to_run_lock = Lock()

        #: dict: Analog output tasks.
        self.analog_outputs = {}

        #: bool: Flag for updating analog task.
        self.is_updating_analog_task = False

        #: str: Trigger mode. Self-trigger or external-trigger.
        self.trigger_mode = "self-trigger"

        #: Any: Device connection.
        self.daq = device_connection

        #: str: microscope name
        self.microscope_name = microscope_name

        #: str: zoom
        self.zoom = self.configuration["experiment"]["MicroscopeState"]["zoom"]

        # retrieves galvo ListProxy/DictProxy from config file
        galvos_raw = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["galvo"]

        # Normalize galvos to always be a list of dicts
        if isinstance(galvos_raw, DictProxy):
            self.galvos = [dict(galvos_raw)]  # wrap single DictProxy into a list
        elif isinstance(galvos_raw, ListProxy):
            self.galvos = [
                dict(g) for g in galvos_raw
            ]  # convert each DictProxy in the list to a dict
        else:
            raise TypeError("Unexpected type for galvos: {}".format(type(galvos_raw)))

        # update analog outputs with galvo IDs and associated axes
        i = 0
        for g in self.galvos:
            self.analog_outputs[f"galvo {i}"] = g["hardware"]["axis"]
            i += 1

        # retreive galvo phases from config
        self.phases = [galvo["phase"] for galvo in self.galvos]

        # update analog outputs with rfvc and associated axis
        remote_focus_channel = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["remote_focus"]["hardware"]["axis"]
        self.analog_outputs["remote_focus"] = remote_focus_channel

        # sets up initial PLC configuration with default delay (ms), camera delay, rfvc delay, sweep time (ms), and analog outputs dict
        self.daq.setup_control_loop([200], 0, 0, 120, self.analog_outputs)

    @classmethod
    def connect(cls, port, baudrate=115200, timeout=0.25):
        """Build ASIDaq Serial Port connection

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

    def prepare_acquisition(self, channel_key: str) -> None:
        """Prepare the acquisition.

        Creates and configures the DAQ tasks.
        Writes the waveforms to each task.

        Parameters
        ----------
        channel_key : str
            Channel key for current channel.
        """
        # Get appropriate sweep_time for the current channel
        sweep_time = self.sweep_times[channel_key]

        # loop through galvo phases to calculate time delays
        # delays[i] corresponds to the time between the ith galvo trigger and the master trigger
        n = len(self.galvos)
        i = 0
        delays = []
        for phase in self.phases:
            frequency = self.waveform_constants["galvo_constants"][f"Galvo {i}"][
                self.microscope_name
            ][self.zoom]["frequency"]
            period = self.exposure_times[channel_key] * 1000 / float(frequency)

            # round period for triangle waveform to even number, as the TG-1000 can only generate triangle waveforms with even-number-of-ms periods
            if self.galvos[i]["waveform"] == "sawtooth":
                rising_ramp = float(
                    self.waveform_constants["galvo_constants"][f"Galvo {i}"][
                        self.microscope_name
                    ][self.zoom].get("rising_ramp", 50)
                )
                if rising_ramp == 50:
                    period = 2 * round(period / 2)

            # round period to closest number of ms, as TG-1000 can only generate waveforms with whole-number-of-ms periods
            period = int(round(period))

            # save first period to sync control loop with first galvo
            if i == 0:
                period0 = period

            # calculate time delay corresponding to phase offset
            t = period * phase / (2 * 3.14159265)
            delays.append(period * (n - i) - t)
            i += 1

        # modify sweep time to sync with the first galvo if there are asi galvos in config
        if len(delays) > 0:
            n7 = 1000 * sweep_time // period0 + 1
            sweep_time = period0 * n7

        self.camera_delay = float(
            self.waveform_constants["other_constants"].get("camera_delay", 5)
        )
        rfvc_delay = float(
            self.waveform_constants["other_constants"].get("remote_focus_delay", 5)
        )
        # sets up control loop with all parameters (all times in ms)
        self.daq.setup_control_loop(
            delays, self.camera_delay, rfvc_delay, sweep_time, self.analog_outputs
        )

        self.current_channel_key = channel_key
        self.is_updating_analog_task = False
        # if self.wait_to_run_lock.locked():
        #     self.wait_to_run_lock.release()

    def run_acquisition(self) -> None:
        """Run DAQ Acquisition.

        Run the tasks for triggering, analog and counter outputs.
        The master trigger initiates all other waveforms via a shared trigger
        For this to work, all analog output and counter tasks have to be primed so that
        they are waiting for the trigger signal.
        """
        # if self.is_updating_analog_task:
        #     self.wait_to_run_lock.acquire()
        #     self.wait_to_run_lock.release()

        # turn on PLC cell 1 (Master Trigger)
        try:
            self.daq.logic_cell_on("1")
        except Exception:
            logger.debug("DAQ cannot turn on")
            pass

    def stop_acquisition(self) -> None:
        """Stop Acquisition.

        Stop control loop.
        """
        # turn on PLC cell 8 (kills control loop)
        # reset PLC cell 1 (Master Trigger)
        try:
            self.daq.logic_cell_on("8")
            self.daq.logic_cell_off("1")
        except Exception:
            logger.debug("DAQ cannot turn off")
            pass

        # if self.wait_to_run_lock.locked():
        #     self.wait_to_run_lock.release()
