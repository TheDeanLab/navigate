# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Imports
import logging
from threading import Lock

# Third Party Imports
import nidaqmx
import numpy as np

# Local Imports
from aslm.model.devices.daq.daq_base import DAQBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class NIDAQ(DAQBase):
    """NIDAQ class for Data Acquisition (DAQ).

    Attributes
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    """

    def __init__(self, configuration):
        super().__init__(configuration)
        self.camera_trigger_task = None
        self.master_trigger_task = None
        try:
            # switching_port = self.configuration["configuration"]["microscopes"][
            #     self.microscope_name
            # ]["daq"]["laser_port_switcher"]
            self.laser_switching_task = nidaqmx.Task()
        except KeyError:
            self.laser_switching_task = None

        self.analog_outputs = {}  # keep track of analog outputs and their waveforms
        self.analog_output_tasks = {}
        self.n_sample = None
        self.current_channel_key = ""
        self.is_updating_analog_task = False
        self.wait_to_run_lock = Lock()

    def __del__(self):
        if self.camera_trigger_task is not None:
            self.stop_acquisition()

    def create_camera_task(self, exposure_time):
        """Set up the camera trigger task.

        Parameters
        ----------
        exposure_time : float
            Duration of camera exposure.
        """
        camera_trigger_out_line = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["camera_trigger_out_line"]
        self.camera_high_time = 0.004  # (self.camera_pulse_percent / 100) *
        # (exposure_time/1000)  # self.sweep_time
        self.camera_low_time = self.sweep_time - self.camera_high_time
        self.camera_delay = (self.camera_delay_percent / 100) * (
            exposure_time / 1000
        )  # * 0.01 * self.sweep_time

        self.camera_trigger_task.co_channels.add_co_pulse_chan_time(
            camera_trigger_out_line,
            high_time=self.camera_high_time,
            low_time=self.camera_low_time,
            initial_delay=self.camera_delay,
        )
        trigger_source = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["trigger_source"]
        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            trigger_source
        )

        if self.configuration['experiment']['MicroscopeState']['image_mode'] == 'confocal-projection':
            n_timepoints = self.configuration['experiment']['MicroscopeState']['timepoints']
            n_timepoints *= self.configuration['experiment']['MicroscopeState']['n_plane']
            print(f"times equals {self.configuration['experiment']['MicroscopeState']['n_plane']} is {n_timepoints}")
            self.camera_trigger_task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=int(n_timepoints))

    def create_master_trigger_task(self):
        """Set up the DO master trigger task."""
        master_trigger_out_line = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["master_trigger_out_line"]
        self.master_trigger_task.do_channels.add_do_chan(
            master_trigger_out_line,
            line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES,
        )

    def create_analog_output_tasks(self, channel_key, create_new_tasks=True):
        """
        Create a single analog output task for all channels per board. Most NI DAQ cards
        have only one clock for analog output sample timing, and as such all channels
        must be grouped here.
        """
        # Create one analog output task per board, grouping the channels
        boards = list(set([x.split("/")[0] for x in self.analog_outputs.keys()]))
        for board in boards:
            channel = ", ".join(
                list(
                    [x for x in self.analog_outputs.keys() if x.split("/")[0] == board]
                )
            )
            if create_new_tasks or self.n_sample is None:
                self.analog_output_tasks[board] = nidaqmx.Task()
                self.analog_output_tasks[board].ao_channels.add_ao_voltage_chan(channel)

                sample_rates = list(
                    set([v["sample_rate"] for v in self.analog_outputs.values()])
                )
                if len(sample_rates) > 1:
                    logger.debug(
                        "NI DAQ - Different sample rates provided for each analog channel."
                        "Defaulting to the first sample rate provided."
                    )
                n_samples = list(set([v["samples"] for v in self.analog_outputs.values()]))
                if len(n_samples) > 1:
                    logger.debug(
                        "NI DAQ - Different number of samples provided for each analog"
                        "channel. Defaulting to the minimum number of samples provided."
                        "Waveforms will be clipped to this length."
                    )
                self.n_sample = min(n_samples)
                if (
                    self.configuration["experiment"]["MicroscopeState"]["image_mode"]
                    == "confocal-projection"
                ):
                    n_timepoints = self.configuration["experiment"]["MicroscopeState"]["timepoints"]
                    n_timepoints *= self.configuration["experiment"]["MicroscopeState"][
                        "n_plane"
                    ]
                    self.analog_output_tasks[board].timing.cfg_samp_clk_timing(
                        rate=sample_rates[0],
                        sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                        samps_per_chan=int(self.n_sample * n_timepoints),
                    )
                else:
                    self.analog_output_tasks[board].timing.cfg_samp_clk_timing(
                        rate=sample_rates[0],
                        sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                        samps_per_chan=self.n_sample,
                    )

                triggers = list(
                    set([v["trigger_source"] for v in self.analog_outputs.values()])
                )
                if len(triggers) > 1:
                    logger.debug(
                        "NI DAQ - Different triggers provided for each analog channel."
                        "Defaulting to the first trigger provided."
                    )
                self.analog_output_tasks[board].triggers.start_trigger.cfg_dig_edge_start_trig(
                    triggers[0]
                )

            # Write values to board
            waveforms = np.vstack(
                [
                    v["waveform"][channel_key][:self.n_sample]
                    for k, v in self.analog_outputs.items()
                    if k.split("/")[0] == board
                ]
            ).squeeze()
            self.analog_output_tasks[board].write(waveforms)

    def prepare_acquisition(self, channel_key, exposure_time):
        """Prepare the acquisition.

        Creates and configures the DAQ tasks.
        Writes the waveforms to each task.

        Parameters
        ----------
        channel_key : int
            Index of channel to be imaged.
        exposure_time : float
            Camera exposure duration.
        """

        self.camera_trigger_task = nidaqmx.Task()
        self.master_trigger_task = nidaqmx.Task()

        # Specify ports, timing, and triggering
        self.create_master_trigger_task()
        self.create_camera_task(exposure_time)
        self.create_analog_output_tasks(channel_key)

        self.current_channel_key = channel_key
        self.is_updating_analog_task = False
        if self.wait_to_run_lock.locked():
            self.wait_to_run_lock.release()

    def run_acquisition(self):
        """Run DAQ Acquisition.

        Run the tasks for triggering, analog and counter outputs.
        The master trigger initiates all other tasks via a shared trigger
        For this to work, all analog output and counter tasks have to be started so that
        they are waiting for the trigger signal."""
        # wait if writing analog tasks
        if self.is_updating_analog_task:
            self.wait_to_run_lock.acquire()
            self.wait_to_run_lock.release()

        self.camera_trigger_task.start()
        for task in self.analog_output_tasks.values():
            task.start()
        self.master_trigger_task.write(
            [False, True, True, True, False], auto_start=True
        )
        # self.camera_trigger_task.wait_until_done()
        for task in self.analog_output_tasks.values():
            task.wait_until_done()
            task.stop()
        try:
            self.camera_trigger_task.stop()
            self.master_trigger_task.stop()
        except nidaqmx.DaqError:
            pass

    def stop_acquisition(self):
        """Stop Acquisition."""
        try:
            self.camera_trigger_task.stop()
            self.master_trigger_task.stop()
            self.camera_trigger_task.close()
            self.master_trigger_task.close()
            for task in self.analog_output_tasks.values():
                task.stop()
                task.close()
        except (AttributeError, nidaqmx.errors.DaqError):
            pass

        if self.wait_to_run_lock.locked():
            self.wait_to_run_lock.release()

        self.analog_output_tasks = {}

    def enable_microscope(self, microscope_name):
        if microscope_name != self.microscope_name:
            self.microscope_name = microscope_name
            self.analog_outputs = {}
            self.analog_output_tasks = {}

        try:
            switching_port = self.configuration["configuration"]["microscopes"][
                self.microscope_name
            ]["daq"]["laser_port_switcher"]
            switching_on_state = self.configuration["configuration"]["microscopes"][
                self.microscope_name
            ]["daq"]["laser_switch_state"]

            self.laser_switching_task.close()
            self.laser_switching_task = nidaqmx.Task()
            self.laser_switching_task.do_channels.add_do_chan(
                switching_port,
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES,
            )
            self.laser_switching_task.write(switching_on_state, auto_start=True)
        except KeyError:
            pass

    def update_analog_task(self, board_name):
        # if there is no such analog task, it means it's not acquiring and nothing needs to do.        
        if board_name not in self.analog_output_tasks:
            return False
        # can't update an analog task while updating one.
        if self.is_updating_analog_task:
            return False
        
        self.wait_to_run_lock.acquire()
        self.is_updating_analog_task = True

        try:
            # this function waits only happens when interacting through GUI in continuous mode,
            # updating an analog task happens after the task is done when running a feature, so it will check and return immediately.
            self.analog_output_tasks[board_name].wait_until_done(timeout=1.0)
            self.analog_output_tasks[board_name].stop()

            # Write values to board
            waveforms = np.vstack(
                [
                    v["waveform"][self.current_channel_key][:self.n_sample]
                    for k, v in self.analog_outputs.items()
                    if k.split("/")[0] == board_name
                ]
            ).squeeze()
            self.analog_output_tasks[board_name].write(waveforms)
        except Exception as e:
            print(f"*** daq error {e} happens!")

        self.is_updating_analog_task = False
        self.wait_to_run_lock.release()