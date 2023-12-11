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

# Third Party Imports
import numpy as np

# Local Imports
from navigate.model.waveforms import remote_focus_ramp


class ConProAcquisition:
    """ConProAcquisition class for controlling continuous acquisition.

    This class provides functionality to control continuous acquisition, including
    managing scan range, offsets, channels, and signal acquisition.

    Notes:
    ------
    - This class is used to control continuous acquisition during microscopy
    experiments, allowing for adjustments in scan range, offsets, and channels.

    - The continuous acquisition process involves initializing parameters, controlling
    signal acquisition, and managing offsets and channels.

    - The `config_table` attribute defines the configuration for the continuous
    acquisition process, including signal acquisition and node type.

    - Does not have multi-position capabilities for now.
    """

    def __init__(self, model, axis="z"):
        """Initialize the ConProAcquisition class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for continuous acquisition control.
        """

        #: MicroscopeModel: The microscope model associated with continuous acquisition.
        self.model = model

        #: str: Stage Axis
        self.axis = axis

        #: float: The scan range for confocal projection acquisition.
        self.scanrange = 0

        #: float: The number of planes for confocal projection acquisition.
        self.n_plane = 0

        #: float: The start offset for confocal projection acquisition.
        self.offset_start = 0

        #: float: The end offset for confocal projection acquisition.
        self.offset_end = 0

        #: float: The offset step size for confocal projection acquisition.
        self.offset_step_size = 0

        #: float: The number of timepoints for confocal projection acquisition.
        self.timepoints = 0

        #: bool: Flag to determine whether to move to a new plane
        self.need_to_move_new_plane = True

        #: float: The time for updating the offset.
        self.offset_update_time = 0

        #: str: The stack cycling mode for confocal projection acquisition.
        self.conpro_cycling_mode = "per_stack"

        #: int: The number of channels in the confocal projection.
        self.channels = [1]

        #: dict: A dictionary defining the configuration for the confocal projection
        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "end": self.signal_end,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_signal_func(self):
        """Initialize continuous acquisition parameters before the signal stage.

        This method initializes continuous acquisition parameters, including scan range,
        offsets, channels, and offset updates, before the signal stage.
        """

        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]

        # microscope_state["conpro_cycling_mode"]
        self.conpro_cycling_mode = "per_stack"
        # get available channel count
        self.channels = microscope_state["selected_channels"]
        #: int: The current channel being acquired in the z-stack
        self.current_channel_in_list = 0

        # get exposure times and sweep times
        galvo_stage = self.model.active_microscope.stages[self.axis]
        sample_rate = galvo_stage.sample_rate
        (
            exposure_times,
            sweep_times,
        ) = self.model.active_microscope.get_exposure_sweep_times()

        # calculate waveforms
        waveform_dict = {}
        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters
                # Assumes Remote Focus Delay < Camera Delay.  Should Assert.
                exposure_time = exposure_times[channel_key]
                sweep_time = sweep_times[channel_key]

                samples = int(sample_rate * sweep_time)

                z_range = microscope_state["scanrange"]
                z_planes = microscope_state["n_plane"]
                z_offset_start = microscope_state["offset_start"]
                z_offset_end = (
                    microscope_state["offset_end"] if z_planes > 1 else z_offset_start
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
                    amp = eval(galvo_stage.volts_per_micron, {"x": 0.5 * (z_range)})
                    off = eval(galvo_stage.volts_per_micron, {"x": 0.5 * (z_offset)})
                    waveforms.append(
                        remote_focus_ramp(
                            sample_rate=galvo_stage.sample_rate,
                            exposure_time=exposure_time,
                            sweep_time=sweep_time,
                            remote_focus_delay=galvo_stage.remote_focus_delay,
                            camera_delay=galvo_stage.camera_delay_percent,
                            fall=galvo_stage.remote_focus_ramp_falling,
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
                waveform_dict[channel_key] = np.hstack(waveforms)
                samples = int(sample_rate * sweep_time * z_planes)
                print(
                    f"Waveform with {z_planes} planes is of length"
                    f" {waveform_dict[channel_key].shape}"
                    f"samples: {samples}"
                )
        galvo_stage.update_waveform(waveform_dict)
        # stop current daq ao tasks
        self.model.active_microscope.daq.stop_acquisition()

    def signal_func(self):
        """Control continuous acquisition and update offsets.

        This method controls the continuous acquisition process, including updating
        offsets and managing signal acquisition during the signal stage.

        Returns:
        -------
        bool
            A boolean value indicating whether to continue the continuous acquisition
            process.
        """

        if self.model.stop_acquisition:
            return False

        # prepare next channel
        if self.current_channel_in_list == 0:
            self.model.active_microscope.current_channel = 0
        self.model.active_microscope.prepare_next_channel()
        return True

    def signal_end(self):
        """Handle the end of the signal stage and offset cycling.

        This method handles the end of the signal stage, including offset cycling and
        timepoint updates for continuous acquisition.

        Returns:
        -------
        bool
            A boolean value indicating whether to end the current node.
        """
        # end this node
        if self.model.stop_acquisition:
            return True

        # decide whether to update offset
        self.current_channel_in_list += 1
        return self.current_channel_in_list >= self.channels
