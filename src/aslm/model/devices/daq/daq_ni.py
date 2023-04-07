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
from aslm.tools.waveform_template_funcs import get_waveform_template_parameters

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class NIDAQ(DAQBase):
    """NIDAQ class for Data Acquisition (DAQ).

    Parameters
    ----------
    configuration : dict
        Global configuration of the microscope

    Attributes
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    waveform_constants : dict
        Dictionary of waveform constants
    microscope_name : str
        Microscope name
    daq_parameters : dict
        Dictionary of DAQ parameters
    sample_rate : float
        Sample rate
    sweep_time : float
        Sweep time
    camera_trigger_task : nidaqmx.Task
        Task for camera triggering
    master_trigger_task : nidaqmx.Task
        Task for master triggering
    trigger_mode : int
        0: self-trigger, 1: external-trigger
    external_trigger : nidaqmx.Task
        Task for external triggering
    laser_switching_task : nidaqmx.Task
        Task for laser switching
    analog_outputs : dict
        Dictionary of analog outputs and their waveforms
    analog_output_tasks : dict
        Dictionary of analog output tasks
    n_sample : int
        Number of samples
    current_channel_key : str
        Current channel key
    is_updating_analog_task : bool
        Flag for updating analog task
    wait_to_run_lock : threading.Lock
        Lock for waiting to run

    Methods
    -------
    calculate_all_waveforms(microscope_name, readout_time)
        Calculate all waveforms
    enable_microscope(microscope_name)
        Enable microscope
    set_external_trigger(external_trigger)
        Set trigger mode
    restart_analog_task_callback()
        Restart analog task callback
    create_camera_task(exposure_time)
        Create camera task
    create_master_trigger_task()
        Create master trigger task
    create_analog_output_tasks(channel_key)
        Create analog output tasks
    prepare_acquisition(channel_key, exposure_time)
        Prepare acquisition
    run_acquisition()
        Run acquisition
    stop_acquisition()
        Stop acquisition
    enable_microscope(microscope_name)
        Enable microscope
    update_analog_task(board_name)
        Update analog task
    """

    def __init__(self, configuration):
        super().__init__(configuration)
        self.camera_trigger_task = None
        self.master_trigger_task = None
        self.trigger_mode = "self-trigger" # self-trigger, external-trigger
        self.external_trigger = None
        try:
            # switching_port = self.configuration["configuration"]["microscopes"][
            #     self.microscope_name
            # ]["daq"]["laser_port_switcher"]
            self.laser_switching_task = nidaqmx.Task()
        except KeyError:
            self.laser_switching_task = None

        # keep track of analog outputs and their waveforms
        self.analog_outputs = {}
        self.analog_output_tasks = {}
        self.n_sample = None
        self.current_channel_key = ""
        self.is_updating_analog_task = False
        self.wait_to_run_lock = Lock()

    def __del__(self):
        """Destructor.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.camera_trigger_task is not None:
            self.stop_acquisition()

    def set_external_trigger(self, external_trigger=None):
        """Set trigger mode.

        Parameters
        ----------
        external_trigger : nidaqmx.Task
            Task for external triggering

        Returns
        -------
        None
        """
        self.trigger_mode = "self-trigger" if external_trigger is None else "external-trigger"
        self.external_trigger = external_trigger

        # change trigger mode during acquisition in a feature
        if self.trigger_mode == "self-trigger":
            self.create_master_trigger_task()
            trigger_source = self.configuration["configuration"]["microscopes"][
            self.microscope_name
            ]["daq"]["trigger_source"]
            # set camera task trigger source
            self.camera_trigger_task.stop()
            self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source
            )
            self.camera_trigger_task.triggers.start_trigger.retriggerable = False
            # set analog task trigger source
            for board_name in self.analog_output_tasks.keys():
                self.analog_output_tasks[board_name].stop()
                self.analog_output_tasks[board_name].triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source)
                self.analog_output_tasks[board_name].register_done_event(None)

        else:
            # close master trigger task
            if self.master_trigger_task:
                self.master_trigger_task.stop()
                self.master_trigger_task.close()
            self.master_trigger_task = None
            # camera task trigger source
            self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(self.external_trigger)
            # change camera task to regeneratable.
            self.camera_trigger_task.triggers.start_trigger.retriggerable = True
            # add callback function to analog tasks
            for board_name in self.analog_output_tasks.keys():
                task = self.analog_output_tasks[board_name]
                task.triggers.start_trigger.cfg_dig_edge_start_trig(self.external_trigger)
                task.register_done_event(None)
                task.register_done_event(self.restart_analog_task_callback_func(task))

    @staticmethod
    def restart_analog_task_callback_func(task):
        """Restart analog task callback function.

        Parameters
        ----------
        task : nidaqmx.Task
            Task for analog output

        Returns
        -------
        callback_func : function
            Callback function
        """
        def callback_func(task_handle, status, callback_data):
            try:
                task.stop()
                task.start()
            except:
                print("*** there is some error when restarting the analog task")
            return status
        return callback_func

    def create_camera_task(self, exposure_time):
        """Set up the camera trigger task.

        Parameters
        ----------
        exposure_time : float
            Duration of camera exposure.

        Returns
        -------
        None
        """
        self.camera_trigger_task = nidaqmx.Task()
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
        # trigger_source = self.configuration["configuration"]["microscopes"][
        #     self.microscope_name
        # ]["daq"]["trigger_source"]
        # self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(
        #     trigger_source
        # )

        # apply waveform templates
        camera_waveform_repeat_num = self.waveform_repeat_num * self.waveform_expand_num
        self.camera_trigger_task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=camera_waveform_repeat_num)

    def create_master_trigger_task(self):
        """Set up the DO master trigger task.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.master_trigger_task = nidaqmx.Task()
        master_trigger_out_line = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["master_trigger_out_line"]
        self.master_trigger_task.do_channels.add_do_chan(
            master_trigger_out_line,
            line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES,
        )

    def create_analog_output_tasks(self, channel_key):
        """Create analog output tasks for each board.

        Create a single analog output task for all channels per board. Most NI DAQ cards
        have only one clock for analog output sample timing, and as such all channels
        must be grouped here.

        Parameters
        ----------
        channel_key : str
            Channel key for analog output.

        Returns
        -------
        None
        """
        n_samples = list(set([v["samples"] for v in self.analog_outputs.values()]))
        if len(n_samples) > 1:
            logger.debug(
                "NI DAQ - Different number of samples provided for each analog"
                "channel. Defaulting to the minimum number of samples provided."
                "Waveforms will be clipped to this length."
            )
        self.n_sample = min(n_samples)
        max_sample = self.n_sample * self.waveform_expand_num
        # TODO: GalvoStage and remote_focus waveform are not calculated based on a same sweep time. There needs some fix.

        # Create one analog output task per board, grouping the channels
        boards = list(set([x.split("/")[0] for x in self.analog_outputs.keys()]))
        for board in boards:
            channel = ", ".join(
                list(
                    [x for x in self.analog_outputs.keys() if x.split("/")[0] == board]
                )
            )
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

            # apply templates to analog tasks
            self.analog_output_tasks[board].timing.cfg_samp_clk_timing(
                rate=sample_rates[0],
                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan=max_sample * self.waveform_repeat_num,
            )

            # triggers = list(
            #     set([v["trigger_source"] for v in self.analog_outputs.values()])
            # )
            # if len(triggers) > 1:
            #     logger.debug(
            #         "NI DAQ - Different triggers provided for each analog channel."
            #         "Defaulting to the first trigger provided."
            #     )
            # self.analog_output_tasks[board].triggers.start_trigger.cfg_dig_edge_start_trig(
            #     triggers[0]
            # )
            # TODO: may change this later to automatically expand the waveform to the longest
            for k, v in self.analog_outputs.items():
                if k.split("/")[0] == board and v["samples"] < max_sample:
                    v["waveform"][channel_key] = np.hstack(
                        [v["waveform"][channel_key]] * self.waveform_expand_num
                    )
            # Write values to board
            waveforms = np.vstack(
                [
                    v["waveform"][channel_key][:max_sample]
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

        Returns
        -------
        None
        """
        waveform_template_name = self.configuration['experiment']['MicroscopeState']["waveform_template"]
        self.waveform_repeat_num, self.waveform_expand_num = get_waveform_template_parameters(
            waveform_template_name,
            self.configuration["waveform_templates"],
            self.configuration['experiment']['MicroscopeState']
        )
        self.create_camera_task(exposure_time)
        self.create_analog_output_tasks(channel_key)

        self.current_channel_key = channel_key
        self.is_updating_analog_task = False
        if self.wait_to_run_lock.locked():
            self.wait_to_run_lock.release()
        # Specify ports, timing, and triggering
        self.set_external_trigger(self.external_trigger)

    def run_acquisition(self):
        """Run DAQ Acquisition.

        Run the tasks for triggering, analog and counter outputs.
        The master trigger initiates all other tasks via a shared trigger
        For this to work, all analog output and counter tasks have to be started so that
        they are waiting for the trigger signal.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # wait if writing analog tasks
        if self.is_updating_analog_task:
            self.wait_to_run_lock.acquire()
            self.wait_to_run_lock.release()

        if self.camera_trigger_task.is_task_done():
            self.camera_trigger_task.start()
            for task in self.analog_output_tasks.values():
                task.start()
        
        if self.trigger_mode == "self-trigger":
            self.master_trigger_task.write(
                [False, True, True, True, False], auto_start=True
            )
        try:
            self.camera_trigger_task.wait_until_done()
            for task in self.analog_output_tasks.values():
                task.wait_until_done()
                if self.trigger_mode == "self-trigger":
                    task.stop()
        except:
            # when triggered from external triggers, sometimes the camera trigger task is done but not actually done, there will a DAQ WARNING message
            pass
        if self.trigger_mode == "self-trigger":
            try:
                self.camera_trigger_task.stop()
                self.master_trigger_task.stop()
            except nidaqmx.DaqError:
                pass

    def stop_acquisition(self):
        """Stop Acquisition.

        Stop all tasks and close them.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        try:
            self.camera_trigger_task.stop()
            self.camera_trigger_task.close()

            if self.trigger_mode == "self-trigger":
                self.master_trigger_task.stop()
                self.master_trigger_task.close()

            for k, task in self.analog_output_tasks.items():
                task.stop()
                task.close()

        except (AttributeError, nidaqmx.errors.DaqError) as e:
            pass

        if self.wait_to_run_lock.locked():
            self.wait_to_run_lock.release()

        self.analog_output_tasks = {}

    def enable_microscope(self, microscope_name):
        """Enable microscope.

        Parameters
        ----------
        microscope_name : str
            Name of microscope to enable.

        Returns
        -------
        None
        """
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
        """Update analog task.

        Parameters
        ----------
        board_name : str
            Name of board to update.

        Returns
        -------
        bool
            True if task is updated, False otherwise.
        """
        # if there is no such analog task,
        # it means it's not acquiring and nothing needs to do.
        if board_name not in self.analog_output_tasks:
            return False
        # can't update an analog task while updating one.
        if self.is_updating_analog_task:
            return False

        self.wait_to_run_lock.acquire()
        self.is_updating_analog_task = True

        try:
            # this function waits only happens when
            # interacting through GUI in continuous mode,

            # updating an analog task happens after the task
            # is done when running a feature, so it will check and return immediately.
            self.analog_output_tasks[board_name].wait_until_done(timeout=1.0)
            self.analog_output_tasks[board_name].stop()

            # Write values to board
            waveforms = np.vstack(
                [
                    v["waveform"][self.current_channel_key][: self.n_sample]
                    for k, v in self.analog_outputs.items()
                    if k.split("/")[0] == board_name
                ]
            ).squeeze()
            self.analog_output_tasks[board_name].write(waveforms)
        except Exception:
            for board in self.analog_output_tasks.keys():
                self.analog_output_tasks[board].stop()
                self.analog_output_tasks[board].close()

            self.create_analog_output_tasks(self.current_channel_key)
            print(f"create new daq analog output task because DAQmx Write failed!")

        self.is_updating_analog_task = False
        self.wait_to_run_lock.release()
