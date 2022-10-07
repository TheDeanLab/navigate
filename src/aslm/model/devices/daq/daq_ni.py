"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard Imports
import logging

# Third Party Imports
import nidaqmx
import numpy as np

# Local Imports
from aslm.model.devices.daq.daq_base import DAQBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class NIDAQ(DAQBase):
    r"""NIDAQ class for Data Acquisition (DAQ).

    Attributes
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope

    """
    def __init__(self, configuration):
        super().__init__(configuration)
        self.camera_trigger_task = None
        self.master_trigger_task = None
        self.laser_switching_task = nidaqmx.Task()

        self.analog_outputs = {}  # keep track of analog outputs and their waveforms
        self.analog_output_tasks = []

    def __del__(self):
        if self.camera_trigger_task is not None:
            self.stop_acquisition()

    def create_camera_task(self, exposure_time):
        r"""Set up the camera trigger task.

        Parameters
        ----------
        exposure_time : float
            Duration of camera exposure.
        """
        camera_trigger_out_line = self.configuration['configuration']['microscopes'][self.microscope_name]['daq']['camera_trigger_out_line']
        self.camera_high_time = 0.004  # (self.camera_pulse_percent / 100) * (exposure_time/1000)  # self.sweep_time
        self.camera_delay = (self.camera_delay_percent / 100) * (exposure_time/1000)  # * 0.01 * self.sweep_time

        self.camera_trigger_task.co_channels.add_co_pulse_chan_time(camera_trigger_out_line,
                                                                    high_time=self.camera_high_time,
                                                                    initial_delay=self.camera_delay)
        trigger_source = self.configuration['configuration']['microscopes'][self.microscope_name]['daq']['trigger_source']
        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source)

    def create_master_trigger_task(self):
        r"""Set up the DO master trigger task."""
        master_trigger_out_line = self.configuration['configuration']['microscopes'][self.microscope_name]['daq']['master_trigger_out_line']
        self.master_trigger_task.do_channels.add_do_chan(master_trigger_out_line,
                                                         line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES)

    def create_analog_output_tasks(self, channel_key):
        """
        Create a single analog output task for all channels per board. Most NI DAQ cards have only one clock for analog
        output sample timing, and as such all channels must be grouped here.
        """

        self.analog_output_tasks = []

        # Create one analog output task per board, grouping the channels
        boards = list(set([x.split('/')[0] for x in self.analog_outputs.keys()]))
        for board in boards:
            channel = ', '.join(list([x for x in self.analog_outputs.keys() if x.split('/')[0] == board]))
            self.analog_output_tasks.append(nidaqmx.Task())
            self.analog_output_tasks[-1].ao_channels.add_ao_voltage_chan(channel)

            sample_rates = list(set([v['sample_rate'] for v in self.analog_outputs.values()]))
            if len(sample_rates) > 1:
                logger.debug("NI DAQ - Different sample rates provided for each analog channel. Defaulting to the first sample rate provided.")
            n_samples = list(set([v['samples'] for v in self.analog_outputs.values()]))
            if len(n_samples) > 1:
                logger.debug("NI DAQ - Different number of samples provided for each analog channel. Defaulting to the minimum number of samples provided. Waveforms will be clipped to this length.")
            n_sample = min(n_samples)
            self.analog_output_tasks[-1].timing.cfg_samp_clk_timing(rate=sample_rates[0],
                                                 sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                                 samps_per_chan=n_sample)

            triggers = list(set([v['trigger_source'] for v in self.analog_outputs.values()]))
            if len(triggers) > 1:
                logger.debug("NI DAQ - Different triggers provided for each analog channel. Defaulting to the first trigger provided.")
            self.analog_output_tasks[-1].triggers.start_trigger.cfg_dig_edge_start_trig(triggers[0])

            # Write values to board
            waveforms = np.vstack([v['waveform'][channel_key][:n_sample] for k, v in self.analog_outputs.items() if k.split('/')[0] == board])
            self.analog_output_tasks[-1].write(waveforms)

    def prepare_acquisition(self, channel_key, exposure_time):
        r"""Prepare the acquisition.

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

    def run_acquisition(self):
        r"""Run DAQ Acquisition.
        Run the tasks for triggering, analog and counter outputs.
        The master trigger initiates all other tasks via a shared trigger
        For this to work, all analog output and counter tasks have to be started so that
        they are waiting for the trigger signal."""
        self.camera_trigger_task.start()
        for task in self.analog_output_tasks:
            task.start()
        self.master_trigger_task.write([False, True, True, True, False], auto_start=True)
        self.camera_trigger_task.wait_until_done()
        for task in self.analog_output_tasks:
            task.wait_until_done()

    def stop_acquisition(self):
        r"""Stop Acquisition."""
        self.camera_trigger_task.stop()
        self.master_trigger_task.stop()
        self.camera_trigger_task.close()
        self.master_trigger_task.close()
        for task in self.analog_output_tasks:
            task.stop()
            task.close()

    def enable_microscope(self, microscope_name):
        if microscope_name != self.microscope_name:
            self.microscope_name = microscope_name
            self.analog_outputs = {}

        switching_port = self.configuration['configuration']['microscopes'][self.microscope_name]['daq']['laser_port_switcher']
        switching_on_state = self.configuration['configuration']['microscopes'][self.microscope_name]['daq']['laser_switch_state']
        
        self.laser_switching_task.close()
        self.laser_switching_task = nidaqmx.Task()
        self.laser_switching_task.do_channels.add_do_chan(
            switching_port, line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES)
        self.laser_switching_task.write(switching_on_state, auto_start=True)
