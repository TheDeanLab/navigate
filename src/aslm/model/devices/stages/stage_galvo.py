# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
import time
from multiprocessing.managers import ListProxy

# Third Party Imports
import numpy as np

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase
from aslm.model.waveforms import dc_value, remote_focus_ramp

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class GalvoNIStage(StageBase):
    """Physik Instrumente Stage Class

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocessing.managers.DictProxy
        Global configuration of the microscope

    Methods
    -------
    create_position_dict()
        Creates a dictionary with the hardware stage positions.
    get_abs_position()
        Makes sure that the move is within the min and max stage limits.
    stop()
        Emergency halt of stage operation.
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)

        # 1 V/ 100 um
        device_config = configuration["configuration"]["microscopes"][microscope_name][
            "stage"
        ]["hardware"]

        # eval(self.volts_per_micron, {"x": 100})
        if type(device_config) == ListProxy:
            self.volts_per_micron = device_config[device_id]["volts_per_micron"]
            self.axes_channels = device_config[device_id]["axes_channels"]
            self.galvo_max_voltage = device_config[device_id]["max"]
            self.galvo_min_voltage = device_config[device_id]["min"]
        else:
            self.volts_per_micron = device_config["volts_per_micron"]
            self.axes_channels = device_config["axes_channels"]
            self.galvo_max_voltage = device_config["max"]
            self.galvo_min_voltage = device_config["min"]

        self.daq = device_connection

        self.microscope_name = microscope_name
        self.configuration = configuration

        self.trigger_source = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]
        self.camera_delay_percent = configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]["delay_percent"]
        self.remote_focus_ramp_falling = configuration["configuration"]["microscopes"][
            microscope_name
        ]["remote_focus_device"]["ramp_falling_percent"]
        self.remote_focus_delay = configuration[
            "configuration"
        ]["microscopes"][microscope_name]["remote_focus_device"]["delay_percent"]
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["sample_rate"]
        self.sweep_time = None
        self.samples = None
        self.readout_time = 0

        self.waveform_dict = {}

    # for stacking, we could have 2 axis here or not, y is for tiling, not necessary
    def report_position(self):
        """Reports the position for all axes, and create position dictionary."""
        return self.get_position_dict()
    
    def calculate_waveform(self, readout_time):
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        volts = eval(
            self.volts_per_micron,
            {"x": self.configuration["experiment"]["StageParameters"][self.axes[0]]},
        )
        self.readout_time = readout_time

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters
                # Assumes Remote Focus Delay < Camera Delay.  Should Assert.
                exposure_time = channel["camera_exposure_time"] / 1000
                self.sweep_time = exposure_time + exposure_time * (
                    (self.camera_delay_percent + self.remote_focus_ramp_falling) / 100
                )

                if readout_time > 0:
                    # This addresses the dovetail nature of the
                    # camera readout in normal mode. The camera reads middle
                    # out, and the delay in start of the last lines
                    # compared to the first lines causes the exposure
                    # to be net longer than exposure_time.
                    # This helps the galvo keep sweeping for the full camera
                    # exposure time.
                    self.sweep_time += readout_time
                self.samples = int(self.sample_rate * self.sweep_time)

                # Calculate the Waveforms
                if (
                    self.configuration["experiment"]["MicroscopeState"]["image_mode"]
                    == "z-stack"
                ):
                    z_start = self.configuration["experiment"]["MicroscopeState"][
                        "abs_z_start"
                    ]
                    z_end = self.configuration["experiment"]["MicroscopeState"][
                        "abs_z_end"
                    ]
                    amp = eval(self.volts_per_micron, {"x": 0.5 * (z_end - z_start)})
                    off = eval(self.volts_per_micron, {"x": 0.5 * (z_end + z_start)})
                    self.waveform_dict[channel_key] = remote_focus_ramp(
                        sample_rate=self.sample_rate,
                        exposure_time=exposure_time,
                        sweep_time=self.sweep_time,
                        remote_focus_delay=self.remote_focus_delay,
                        camera_delay=self.camera_delay_percent,
                        fall=self.remote_focus_ramp_falling,
                        amplitude=amp,
                        offset=off,
                    )
                elif (
                    self.configuration["experiment"]["MicroscopeState"]["image_mode"]
                    == "confocal-projection"
                ):
                    z_range = microscope_state["scanrange"]
                    z_planes = microscope_state["n_plane"]
                    z_offset_start = microscope_state["offset_start"]
                    z_offset_end = (
                        microscope_state["offset_end"]
                        if z_planes > 1
                        else z_offset_start
                    )
                    waveforms = []
                    if z_planes > 1:
                        offsets = (
                            np.arange(int(z_planes))
                            * (z_offset_end - z_offset_start)
                            / float(z_planes - 1)
                        )
                    else:
                        offsets = [z_offset_start]
                    print(offsets)
                    for z_offset in offsets:
                        amp = eval(self.volts_per_micron, {"x": 0.5 * (z_range)})
                        off = eval(self.volts_per_micron, {"x": 0.5 * (z_offset)})
                        waveforms.append(
                            remote_focus_ramp(
                                sample_rate=self.sample_rate,
                                exposure_time=exposure_time,
                                sweep_time=self.sweep_time,
                                remote_focus_delay=self.remote_focus_delay,
                                camera_delay=self.camera_delay_percent,
                                fall=self.remote_focus_ramp_falling,
                                amplitude=amp,
                                offset=off,
                            )
                        )
                        print(waveforms[-1].shape)
                        print(
                            np.min(waveforms[-1]),
                            np.mean(waveforms[-1]),
                            np.max(waveforms[-1]),
                        )
                    self.waveform_dict[channel_key] = np.hstack(waveforms)
                    self.samples = int(self.sample_rate * self.sweep_time * z_planes)
                    print(
                        f"Waveform with {z_planes} planes is of length"
                        f" {self.waveform_dict[channel_key].shape}"
                    )
                else:
                    self.waveform_dict[channel_key] = dc_value(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        amplitude=volts,
                    )
                
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] > self.galvo_max_voltage
                ] = self.galvo_max_voltage
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] < self.galvo_min_voltage
                ] = self.galvo_min_voltage

        self.daq.analog_outputs[self.axes_channels[0]] = {
            "sample_rate": self.sample_rate,
            "samples": self.samples,
            "trigger_source": self.trigger_source,
            "waveform": self.waveform_dict,
        }
        return self.waveform_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """Implement movement logic along a single axis.

        Example calls:

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary.
            For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement.
            Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expect values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        bool
            Was the move successful?
        """
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        volts = eval(self.volts_per_micron, {"x": axis_abs})

        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        # duty wait duration
        duty_cycle_wait_duration = (
            float(
                self.configuration["waveform_constants"]
                .get("other_constants", {})
                .get("remote_focus_settle_duration", 0)
            )
            / 1000
        )

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters
                # Assumes Remote Focus Delay < Camera Delay.  Should Assert.
                exposure_time = channel["camera_exposure_time"] / 1000
                self.sweep_time = exposure_time + exposure_time * (
                    (self.camera_delay_percent + self.remote_focus_ramp_falling) / 100
                )
                if self.readout_time > 0:
                    # This addresses the dovetail nature of the
                    # camera readout in normal mode. The camera reads middle
                    # out, and the delay in start of the last lines
                    # compared to the first lines causes the exposure
                    # to be net longer than exposure_time.
                    # This helps the galvo keep sweeping for the full camera
                    # exposure time.
                    self.sweep_time += self.readout_time

                self.sweep_time += duty_cycle_wait_duration

                self.samples = int(self.sample_rate * self.sweep_time)

                # Calculate the Waveforms
                self.waveform_dict[channel_key] = dc_value(
                    sample_rate=self.sample_rate,
                    sweep_time=self.sweep_time,
                    amplitude=volts,
                )
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] > self.galvo_max_voltage
                ] = self.galvo_max_voltage
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] < self.galvo_min_voltage
                ] = self.galvo_min_voltage

        self.daq.analog_outputs[self.axes_channels[axis_num]] = {
            "sample_rate": self.sample_rate,
            "samples": self.samples,
            "trigger_source": self.trigger_source,
            "waveform": self.waveform_dict,
        }
        # update analog waveform
        self.daq.update_analog_task(self.axes_channels[axis_num].split("/")[0])

        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
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
        result = True
        for i, ax in enumerate(self.axes):
            success = self.move_axis_absolute(ax, i, move_dictionary)
            if success and wait_until_done is True:
                stage_pos, n_tries, i = -1e50, 10, 0
                target_pos = move_dictionary[f"{ax}_abs"]
                while (abs(stage_pos - target_pos) < 0.01) and (i < n_tries):
                    #  replace: stage_pos =
                    #  self.mcl_controller.MCL_SingleReadN(ax, self.handle)
                    #  todo: include a call to the NI board to set a voltage
                    i += 1
                    time.sleep(0.01)
                if abs(stage_pos - target_pos) > 0.01:
                    success = False
                else:
                    setattr(self, f"{ax}_pos", target_pos)
            result = result and success
        return result

    def stop(self):
        """Stop all stage movement abruptly."""
        pass
