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

from pathlib import Path
import multiprocessing as mp
from multiprocessing import Manager
import threading
import time

# Third Party Imports
import numpy as np
import random

# Local Imports
from aslm.config.config import load_configs, verify_configuration
from aslm.model.devices.camera.camera_synthetic import (
    SyntheticCamera,
    SyntheticCameraController,
)
from aslm.model.features.feature_container import (
    load_features,
)


class DummyController:
    def __init__(self, view):
        """Initialize the Dummy controller.

        Args
        ----
        view : DummyView
            The view to be controlled by this controller.

        Returns
        -------
        None

        Example
        -------
        >>> controller = DummyController(view)
        """
        from aslm.controller.configuration_controller import ConfigurationController

        self.configuration = DummyModel().configuration
        self.commands = []
        self.view = view
        self.configuration_controller = ConfigurationController(self.configuration)
        self.stage_pos = {}
        self.off_stage_pos = {}

    def execute(self, str, sec=None, *args):
        """Execute a command.

        Appends commands sent via execute,
        first element is oldest command/first to pop off


        Args
        ----
        str : str
            The command to be executed.
        sec : float
            The time to wait before executing the command.

        Returns
        -------
        None

        Example
        -------
        >>> controller.execute('move_stage', 1)
        """

        self.commands.append(str)
        if sec is not None:
            self.commands.append(sec)

        if str == "get_stage_position":
            self.stage_pos["x"] = int(random.random())
            self.stage_pos["y"] = int(random.random())
            return self.stage_pos

    def pop(self):
        """Pop the oldest command.

        Use this method in testing code to grab the next command.

        Parameters
        ----------
        None

        Returns
        -------
        str
            The oldest command.

        Example
        -------
        >>> controller.pop()
        """

        if len(self.commands) > 0:
            return self.commands.pop(0)
        else:
            return "Empty command list"

    def clear(self):
        """Clear command list"""
        self.commands = []


class DummyModel:
    """Dummy Model

    This class is used to test the controller and view.

    Attributes
    ----------
    configuration : Configuration
        The configuration object.
    signal_container : SignalContainer
        The signal container.
    data_container : DataContainer
        The data container.
    signal_pipe : Pipe
        The pipe for sending signals.
    data_pipe : Pipe
        The pipe for sending data.
    signal_thread : Thread
        The thread for sending signals.
    data_thread : Thread
        The thread for sending data.
    stop_flag : bool
        The flag for stopping the threads.
    frame_id : int
        The frame id.
    data : list
        The list of data.

    Methods
    -------
    signal_func()
        The function for sending signals.
    data_func()
        The function for sending data.

    Example
    -------
    >>> model = DummyModel()
    """

    def __init__(self):
        # Set up the model, experiment, waveform dictionaries
        base_directory = Path(__file__).resolve().parent.parent
        configuration_directory = Path.joinpath(base_directory, "config")

        config = Path.joinpath(configuration_directory, "configuration.yaml")
        experiment = Path.joinpath(configuration_directory, "experiment.yml")
        waveform_constants = Path.joinpath(
            configuration_directory, "waveform_constants.yml"
        )

        self.manager = Manager()
        self.configuration = load_configs(
            self.manager,
            configuration=config,
            experiment=experiment,
            waveform_constants=waveform_constants,
        )

        verify_configuration(self.manager, self.configuration)

        self.device = DummyDevice()
        self.signal_pipe, self.data_pipe = None, None

        self.active_microscope = DummyMicroscope(
            "Mesoscale", self.configuration, devices_dict={}, is_synthetic=True
        )

        self.signal_container = None
        self.data_container = None
        self.signal_thread = None
        self.data_thread = None

        self.stop_flag = False
        self.frame_id = 0  # signal_num

        self.data = []
        self.signal_records = []
        self.data_records = []

        self.img_width = int(
            self.configuration["experiment"]["CameraParameters"]["x_pixels"]
        )
        self.img_height = int(
            self.configuration["experiment"]["CameraParameters"]["y_pixels"]
        )
        self.number_of_frames = 10
        self.data_buffer = np.zeros(
            (self.number_of_frames, self.img_width, self.img_height)
        )
        self.data_buffer_positions = np.zeros(
            shape=(self.number_of_frames, 5), dtype=float
        )  # z-index, x, y, z, theta, f

        self.camera = {}
        self.active_microscope_name = self.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]
        for k in self.configuration["configuration"]["microscopes"].keys():
            self.camera[k] = SyntheticCamera(
                self.active_microscope_name,
                SyntheticCameraController(),
                self.configuration,
            )
            self.camera[k].initialize_image_series(
                self.data_buffer, self.number_of_frames
            )

    def signal_func(self):
        self.signal_container.reset()
        while not self.signal_container.end_flag:
            if self.signal_container:
                self.signal_container.run()

            self.signal_pipe.send("signal")
            self.signal_pipe.recv()

            if self.signal_container:
                self.signal_container.run(wait_response=True)

            self.frame_id += 1  # signal_num

        self.signal_pipe.send("shutdown")

        self.stop_flag = True

    def data_func(self):
        """The function for sending data.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Example
        -------
        >>> model.data_func()
        """
        while not self.stop_flag:
            self.data_pipe.send("getData")
            frame_ids = self.data_pipe.recv()
            print("receive: ", frame_ids)
            if not frame_ids:
                continue

            self.data.append(frame_ids)

            if self.data_container:
                self.data_container.run(frame_ids)
        self.data_pipe.send("shutdown")

    def start(self, feature_list):
        """Start the model.

        Parameters
        ----------
        feature_list : list
            The list of features to be used.

        Returns
        -------
        None

        Example
        -------
        >>> model.start(['signal', 'data'])
        """

        if feature_list is None:
            return False
        self.data = []
        self.signal_records = []
        self.data_records = []
        self.stop_flag = False
        self.frame_id = 0  # signal_num

        self.signal_pipe, self.data_pipe = self.device.setup()

        self.signal_container, self.data_container = load_features(self, feature_list)
        self.signal_thread = threading.Thread(target=self.signal_func, name="signal")
        self.data_thread = threading.Thread(target=self.data_func, name="data")
        self.signal_thread.start()
        self.data_thread.start()

        self.signal_thread.join()
        self.stop_flag = True
        self.data_thread.join()

        return True


class DummyDevice:
    """Dummy Device

    This class is used to test the controller and view.

    Attributes
    ----------
    signal_pipe : Pipe
        The pipe for sending signals.
    data_pipe : Pipe
        The pipe for sending data.

    Methods
    -------
    setup()
        Set up the pipes.
    shutdown()
        Shutdown the pipes.

    Example
    -------
    >>> device = DummyDevice()
    """

    def __init__(self, timecost=0.2):
        self.msg_count = mp.Value("i", 0)
        self.sendout_msg_count = 0
        self.out_port = None
        self.in_port = None
        self.timecost = timecost
        self.stop_flag = False

    def setup(self):
        """Set up the pipes.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Example
        -------
        >>> device.setup()
        """

        signalPort, self.in_port = mp.Pipe()
        dataPort, self.out_port = mp.Pipe()
        in_process = mp.Process(target=self.listen)
        out_process = mp.Process(target=self.sendout)
        in_process.start()
        out_process.start()

        self.sendout_msg_count = 0
        self.msg_count.value = 0
        self.stop_flag = False

        return signalPort, dataPort

    def generate_message(self):
        """Generate a message.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Example
        -------
        >>> device.generate_message()
        """

        time.sleep(self.timecost)
        self.msg_count.value += 1

    def clear(self):
        """Clear the pipes.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Example
        -------
        >>> device.clear()
        """
        self.msg_count.value = 0

    def listen(self):
        """Listen to the pipe.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Example
        -------
        >>> device.listen()
        """
        while not self.stop_flag:
            signal = self.in_port.recv()
            if signal == "shutdown":
                self.stop_flag = True
                self.in_port.close()
                break
            self.generate_message()
            self.in_port.send("done")

    def sendout(self, timeout=100):
        """Send out the message.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Example
        -------
        >>> device.sendout()
        """
        while not self.stop_flag:
            msg = self.out_port.recv()
            if msg == "shutdown":
                self.out_port.close()
                break
            c = 0
            while self.msg_count.value == self.sendout_msg_count and c < timeout:
                time.sleep(0.01)
                c += 1
            self.out_port.send(
                list(range(self.sendout_msg_count, self.msg_count.value))
            )
            self.sendout_msg_count = self.msg_count.value


class DummyMicroscope:
    """Dummy Microscope

    This class is used to test the controller and view.

    Attributes
    ----------
    signal_pipe : Pipe
        The pipe for sending signals.
    data_pipe : Pipe
        The pipe for sending data.

    Methods
    -------
    setup()
        Set up the pipes.
    shutdown()
        Shutdown the pipes.

    Example
    -------
    >>> device = DummyMicroscope()
    """

    def __init__(self, name, configuration, devices_dict, is_synthetic=False):
        self.microscope_name = name
        self.configuration = configuration
        self.data_buffer = None
        self.stages = {}
        self.lasers = {}
        self.galvo = {}
        self.daq = devices_dict.get("daq", None)
        self.current_channel = 0

    def calculate_exposure_sweep_times(self, readout_time=0):
        """Get the exposure and sweep times for all channels.

        Parameters
        ----------
        readout_time : float
            Readout time of the camera (seconds) if we are operating the camera in
            Normal mode, otherwise -1.
        """
        exposure_times = {}
        sweep_times = {}
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        zoom = microscope_state["zoom"]
        waveform_constants = self.configuration["waveform_constants"]
        camera_delay_percent = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["camera"]["delay_percent"]
        remote_focus_ramp_falling = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["remote_focus_device"]["ramp_falling_percent"]

        duty_cycle_wait_duration = (
            float(
                self.configuration["waveform_constants"]
                .get("other_constants", {})
                .get("remote_focus_settle_duration", 0)
            )
            / 1000
        )
        for channel_key in microscope_state["channels"].keys():
            channel = microscope_state["channels"][channel_key]
            if channel["is_selected"] is True:
                exposure_time = channel["camera_exposure_time"] / 1000

                sweep_time = (
                    exposure_time
                    + exposure_time
                    * (camera_delay_percent + remote_focus_ramp_falling)
                    / 100
                )
                if readout_time > 0:
                    # This addresses the dovetail nature of the camera readout in normal
                    # mode. The camera reads middle out, and the delay in start of the
                    # last lines compared to the first lines causes the exposure to be
                    # net longer than exposure_time. This helps the galvo keep sweeping
                    # for the full camera exposure time.
                    sweep_time += readout_time  # we could set it to 0.14 instead of
                    # 0.16384 according to the test

                ps = float(
                    waveform_constants["remote_focus_constants"][self.microscope_name][
                        zoom
                    ][channel["laser"]].get("percent_smoothing", 0.0)
                )
                if ps > 0:
                    sweep_time = (1 + ps / 100) * sweep_time

                sweep_time += duty_cycle_wait_duration

                exposure_times[channel_key] = exposure_time
                sweep_times[channel_key] = sweep_time

        return exposure_times, sweep_times
