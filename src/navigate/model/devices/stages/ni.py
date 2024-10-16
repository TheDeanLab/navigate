# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:
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

# Standard Library Imports
import logging
import traceback
from multiprocessing.managers import ListProxy
import time
from typing import Any, Dict

# Third Party Imports
import numpy as np
import nidaqmx

# Local Imports
from navigate.model.devices.stages.base import StageBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class GalvoNIStage(StageBase):
    """Galvo Stage Class (only supports one axis)

    Generic analog controlled stage. Could be used to control piezoelectric devices,
    galvos, etc. Currently set up to handle National Instruments data acquisition cards.

    Retrieves the volts per micron from the configuration file and uses that to
    determine the correct voltage to send to the stage.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the Galvo Stage.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        device_id : int
            Device ID of the stage
        """
        super().__init__(microscope_name, device_connection, configuration, device_id)

        # 1 V/ 100 um
        device_config = configuration["configuration"]["microscopes"][microscope_name][
            "stage"
        ]["hardware"]

        if type(device_config) == ListProxy:
            #: float: volts per micron scaling factor.
            self.volts_per_micron = device_config[device_id]["volts_per_micron"]

            #: int: channel number for each axis
            self.axes_channels = device_config[device_id]["axes_mapping"]

            #: float: maximum voltage for each axis
            self.galvo_max_voltage = device_config[device_id]["max"]

            #: float: minimum voltage for each axis
            self.galvo_min_voltage = device_config[device_id]["min"]

            #: float: Distance threshold for wait until delay
            self.distance_threshold = device_config[device_id].get(
                "distance_threshold", None
            )  # microns

            #: float: Stage settle duration in milliseconds.
            self.stage_settle_duration = (
                device_config[device_id].get("settle_duration_ms", 20) / 1000
            )  # convert to seconds
        else:
            self.volts_per_micron = device_config["volts_per_micron"]
            self.axes_channels = device_config["axes_mapping"]
            self.galvo_max_voltage = device_config["max"]
            self.galvo_min_voltage = device_config["min"]
            self.distance_threshold = device_config.get("distance_threshold", None)
            self.stage_settle_duration = (
                device_config.get("settle_duration_ms", 20) / 1000
            )

        #: dict: Mapping of software axes to hardware axes.
        self.axes_mapping = {self.axes[0]: self.axes_channels[0]}

        #: object: Hardware device to connect to.
        self.daq = device_connection

        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: multiprocessing.managers.DictProxy: Global configuration of the microscope.
        self.configuration = configuration

        #: str: Trigger source for the DAQ.
        self.trigger_source = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]

        #: float: Percent of the camera delay.
        self.camera_delay = (
            configuration["configuration"]["microscopes"][microscope_name]["camera"][
                "delay"
            ]
            / 1000
        )

        #: float: Sample rate of the DAQ.
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["sample_rate"]

        #: dict: Dictionary of exposure times for each channel.
        self.exposure_times = None

        #: dict: Dictionary of sweep times for each channel.
        self.sweep_times = None

        #: dict: Dictionary of waveforms for each channel.
        self.waveform_dict = {}

        #: object: DAQ ao task
        self.ao_task = None

        self.switch_mode("normal")

    # for stacking, we could have 2 axis here or not, y is for tiling, not necessary
    def report_position(self):
        """Reports the position for all axes, and create position dictionary.

        Returns
        -------
        dict
            Dictionary of positions for each axis.
        """
        return self.get_position_dict()

    def update_waveform(self, waveform_dict):
        """Update the waveform for the stage.

        Parameters
        ----------
        waveform_dict : dict
            Dictionary of waveforms for each channel

        Returns
        -------
        result : bool
            success or failed
        """
        self.switch_mode("waveform")
        microscope_state = self.configuration["experiment"]["MicroscopeState"]

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                if channel_key not in waveform_dict:
                    logger.debug(f"Update waveform in StageGalvo failed! {channel_key}")
                    print("*** updating waveform in StageGalvo failed!", channel_key)
                    return False

                waveform_dict[channel_key][
                    waveform_dict[channel_key] > self.galvo_max_voltage
                ] = self.galvo_max_voltage
                waveform_dict[channel_key][
                    waveform_dict[channel_key] < self.galvo_min_voltage
                ] = self.galvo_min_voltage

        self.waveform_dict = waveform_dict
        self.daq.analog_outputs[self.axes_channels[0]] = {
            "trigger_source": self.trigger_source,
            "waveform": self.waveform_dict,
        }
        return True

    def move_axis_absolute(self, axis, abs_pos, wait_until_done=False):
        """Implement movement logic along a single axis.

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary.
            For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        abs_pos : float
            Absolute position value
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        bool
            Was the move successful?
        """
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        axis_abs = self.get_abs_position(axis, abs_pos)
        if axis_abs == -1e50:
            return False

        # Keep track of step size.
        current_position = getattr(self, f"{axis}_pos", axis_abs)
        delta_position = np.abs(axis_abs - current_position)

        volts = eval(self.volts_per_micron, {"x": axis_abs})
        if volts > self.galvo_max_voltage:
            volts = self.galvo_max_voltage
        if volts < self.galvo_min_voltage:
            volts = self.galvo_min_voltage

        try:
            self.ao_task.write(volts, auto_start=True)
        except Exception as e:
            logger.debug(f"Error moving {axis} to {axis_abs} volts: {volts}")
            logger.exception(e)
        # Stage Settle Duration in Milliseconds
        if (
            wait_until_done
            and (self.distance_threshold is not None)
            and (delta_position >= self.distance_threshold)
        ):
            time.sleep(self.stage_settle_duration)

        setattr(self, f"{axis}_pos", axis_abs)

        return True

    def move_absolute(self, move_dictionary, wait_until_done=True):
        """Move Absolute Method.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement.
            Includes 'x_abs', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """
        abs_pos_dict = self.verify_abs_position(move_dictionary)
        if not abs_pos_dict:
            return False
        axis = list(abs_pos_dict.keys())[0]
        return self.move_axis_absolute(axis, abs_pos_dict[axis], wait_until_done)

    def stop(self):
        """Stop all stage movement abruptly."""
        pass

    def switch_mode(self, mode="normal", exposure_times=None, sweep_times=None):
        """Switch Galvo stage working mode.

        Parameters
        ----------
        mode : str
            Name of the stage working mode
            Current supported modes are: confocal-projection, normal
        exposure_times : dict
            Dictionary of exposure times for each channel
        sweep_times : dict
            Dictionary of sweep times for each channel
        """
        self.exposure_times = exposure_times
        self.sweep_times = sweep_times
        if mode == "normal":
            if self.ao_task is None:
                self.ao_task = nidaqmx.Task()
                self.ao_task.ao_channels.add_ao_voltage_chan(self.axes_channels[0])
            self.move_axis_absolute(
                self.axes[0],
                float(
                    self.configuration["experiment"]["StageParameters"][self.axes[0]]
                ),
            )
        elif self.ao_task:
            self.ao_task.stop()
            self.ao_task.close()
            self.ao_task = None

    def close(self) -> None:
        """Close the Galvo stage."""
        if self.ao_task:
            try:
                self.ao_task.stop()
                self.ao_task.close()
            except Exception:
                logger.exception(f"Error stopping task: {traceback.format_exc()}")

    def __del__(self) -> None:
        """Close the Galvo stage."""
        self.close()
