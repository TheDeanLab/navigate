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
from navigate.config.config import (
    load_configs,
    verify_experiment_config,
    verify_waveform_constants,
    verify_configuration,
)
from navigate.model.devices.camera.camera_synthetic import (
    SyntheticCamera,
    SyntheticCameraController,
)
from navigate.model.features.feature_container import (
    load_features,
)


class DummyController:
    """Dummy Controller"""

    def __init__(self, view):
        """Initialize the Dummy controller.

        Parameters
        ----------
        view : DummyView
            The view to be controlled by this controller.

        Example
        -------
        >>> controller = DummyController(view)
        """
        from navigate.controller.configuration_controller import ConfigurationController
        from navigate.controller.sub_controllers import MenuController
        from navigate.controller.sub_controllers.multi_position_controller import (
            MultiPositionController,
        )
        from navigate.controller.sub_controllers.channels_tab_controller import (
            ChannelsTabController,
        )

        #: dict: The configuration dictionary.
        self.configuration = DummyModel().configuration
        #: list: The list of commands.
        self.commands = []
        #: DummyView: The view to be controlled by this controller.
        self.view = view
        #: ConfigurationController: The configuration controller.
        self.configuration_controller = ConfigurationController(self.configuration)
        #: MenuController: The menu controller.
        self.menu_controller = MenuController(view=self.view, parent_controller=self)
        self.channels_tab_controller = ChannelsTabController(
            self.view.settings.channels_tab, self
        )
        self.multiposition_tab_controller = MultiPositionController(
            self.view.settings.multiposition_tab.multipoint_list, self
        )
        #: dict: The stage positions.
        self.stage_pos = {}
        #: dict: The stage offset positions.
        self.off_stage_pos = {}
        base_directory = Path.joinpath(Path(__file__).resolve().parent.parent)
        configuration_directory = Path.joinpath(base_directory, "config")
        self.waveform_constants_path = Path.joinpath(
            configuration_directory, "waveform_constants.yml"
        )

    def execute(self, str, sec=None, *args):
        """Execute a command.

        Appends commands sent via execute,
        first element is oldest command/first to pop off

        Parameters
        ----------
        str : str
            The command to be executed.
        sec : float
            The time to wait before executing the command.

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
    """Dummy Model - This class is used to test the controller and view."""

    def __init__(self):
        """Initialize the Dummy model."""
        # Set up the model, experiment, waveform dictionaries
        base_directory = Path(__file__).resolve().parent.parent.parent
        configuration_directory = Path.joinpath(base_directory,
                                                "src",
                                                "navigate",
                                                "config")

        config = Path.joinpath(configuration_directory, "configuration.yaml")
        experiment = Path.joinpath(configuration_directory, "experiment.yml")
        waveform_constants = Path.joinpath(
            configuration_directory, "waveform_constants.yml"
        )

        #: Manager: The manager.
        self.manager = Manager()
        #: dict: The configuration dictionary.
        self.configuration = load_configs(
            self.manager,
            configuration=config,
            experiment=experiment,
            waveform_constants=waveform_constants,
        )

        verify_configuration(self.manager, self.configuration)
        verify_experiment_config(self.manager, self.configuration)
        verify_waveform_constants(self.manager, self.configuration)

        #: DummyDevice: The device.
        self.device = DummyDevice()
        #: Pipe: The pipe for sending signals.
        self.signal_pipe, self.data_pipe = None, None
        #: DummyMicroscope: The microscope.
        self.active_microscope = DummyMicroscope(
            "Mesoscale", self.configuration, devices_dict={}, is_synthetic=True
        )
        #: Object: The signal container.
        self.signal_container = None
        #: Object: The data container.
        self.data_container = None
        #: Thread: The signal thread.
        self.signal_thread = None
        #: Thread: The data thread.
        self.data_thread = None

        #: bool: The flag for stopping the model.
        self.stop_flag = False
        #: int: The frame id.
        self.frame_id = 0  # signal_num
        #: list: The list of data.
        self.data = []
        #: list: The list of signal records.
        self.signal_records = []
        #: list: The list of data records.
        self.data_records = []
        #: int: The image width.
        self.img_width = int(
            self.configuration["experiment"]["CameraParameters"]["x_pixels"]
        )
        #: int: The image height.
        self.img_height = int(
            self.configuration["experiment"]["CameraParameters"]["y_pixels"]
        )
        #: int: The number of frames in the data buffer.
        self.number_of_frames = 10
        #: ndarray: The data buffer.
        self.data_buffer = np.zeros(
            (self.number_of_frames, self.img_width, self.img_height)
        )
        #: ndarray: The data buffer positions.
        self.data_buffer_positions = np.zeros(
            shape=(self.number_of_frames, 5), dtype=float
        )  # z-index, x, y, z, theta, f
        #: dict: The camera dictionary.
        self.camera = {}
        #: str: The active microscope name.
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
        """Perform signal-related functionality.

        This method is responsible for signal processing operations. It resets the
        signal container and continues processing signals until the end flag is set.
        During each iteration, it runs the signal container and communicates with
        a separate process using a signal pipe. The `frame_id` is incremented after
        each signal processing step.

        Note
        ----
        - The function utilizes a signal container and a signal pipe for communication.
        - It terminates when the `end_flag` is set and sends a "shutdown" signal.
        """

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
        """The function responsible for sending and processing data.

        This method continuously sends data requests using a data pipe and receives
        corresponding frame IDs. It appends the received frame IDs to the data storage
        and runs data processing operations if a data container is available.

        Notes
        -----
        - The function operates in a loop until the `stop_flag` is set.
        - It communicates with a separate process using a data pipe for data retrieval.
        - Received frame IDs are appended to the data storage and processed if
        applicable.
        - The method terminates by sending a "shutdown" signal.

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
        bool
            True if the model is started successfully, False otherwise.

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
    """Dummy Device - class is used to test the controller and view."""

    def __init__(self, timecost=0.2):
        """Initialize the Dummy device.

        Parameters
        ----------
        timecost : float
            The time cost for generating a message.
        """

        #: int: The message count.
        self.msg_count = mp.Value("i", 0)
        #: int: The sendout message count.
        self.sendout_msg_count = 0
        #: Pipe: The pipe for sending signals.
        self.out_port = None
        #: Pipe: The pipe for receiving signals.
        self.in_port = None
        #: float: The time cost for generating a message.
        self.timecost = timecost
        #: bool: The flag for stopping the device.
        self.stop_flag = False

    def setup(self):
        """Set up the pipes.

        Returns
        -------
        Pipe
            The pipe for sending signals.
        Pipe
            The pipe for receiving signals.

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

        Example
        -------
        >>> device.generate_message()
        """

        time.sleep(self.timecost)
        self.msg_count.value += 1

    def clear(self):
        """Clear the pipes.

        Example
        -------
        >>> device.clear()
        """
        self.msg_count.value = 0

    def listen(self):
        """Listen to the pipe.

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
        timeout : int
            The timeout for sending out the message.

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
    """Dummy Microscope - Class is used to test the controller and view."""

    def __init__(self, name, configuration, devices_dict, is_synthetic=False):
        """Initialize the Dummy microscope.

        Parameters
        ----------
        name : str
            The microscope name.
        configuration : dict
            The configuration dictionary.
        devices_dict : dict
            The dictionary of devices.
        is_synthetic : bool
            The flag for using a synthetic microscope.
        """
        #: str: The microscope name.
        self.microscope_name = name
        #: dict: The configuration dictionary.
        self.configuration = configuration
        #: np.ndarray: The data buffer.
        self.data_buffer = None
        #: dict: The stage dictionary.
        self.stages = {}
        #: dict: The lasers dictionary.
        self.lasers = {}
        #: dict: The galvo dictionary.
        self.galvo = {}
        #: dict: The DAQ dictionary.
        self.daq = devices_dict.get("daq", None)
        #: int: The current channel.
        self.current_channel = 0
        self.camera = SyntheticCamera(
            self.configuration["experiment"]["MicroscopeState"]["microscope_name"],
            SyntheticCameraController(),
            self.configuration,
        )

    def calculate_exposure_sweep_times(self):
        """Get the exposure and sweep times for all channels.

        Returns
        -------
        dict
            The dictionary of exposure times.
        dict
            The dictionary of sweep times.
        """
        exposure_times = {}
        sweep_times = {}
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        zoom = microscope_state["zoom"]
        waveform_constants = self.configuration["waveform_constants"]
        camera_delay = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["camera"]["delay"] / 1000
        camera_settle_duration = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["camera"].get("settle_duration", 0) / 1000
        remote_focus_ramp_falling = float(
                waveform_constants["other_constants"]["remote_focus_ramp_falling"]
            ) / 1000

        duty_cycle_wait_duration = (
            float(
                waveform_constants["other_constants"]["remote_focus_settle_duration"]
            ) / 1000
        )
        ps = float(
            waveform_constants["other_constants"].get("percent_smoothing", 0.0)
        )

        readout_time = 0
        readout_mode = self.configuration["experiment"]["CameraParameters"]["sensor_mode"]
        if readout_mode == "Normal":
            readout_time = self.camera.calculate_readout_time()
        elif (
            self.configuration["experiment"]["CameraParameters"]["readout_direction"] in ["Bidirectional", "Rev. Bidirectional"]
        ):
            remote_focus_ramp_falling = 0
        # set readout out time
        self.configuration["experiment"]["CameraParameters"]["readout_time"] = readout_time * 1000
        for channel_key in microscope_state["channels"].keys():
            channel = microscope_state["channels"][channel_key]
            if channel["is_selected"] is True:
                exposure_time = channel["camera_exposure_time"] / 1000

                if readout_mode == "Light-Sheet":
                    _, _, updated_exposure_time = self.camera.calculate_light_sheet_exposure_time(
                        exposure_time,
                        int(
                            self.configuration["experiment"]["CameraParameters"][
                                "number_of_pixels"
                            ]
                        )
                    )
                    if updated_exposure_time != exposure_time:
                        print(f"*** Notice: The actual exposure time of the camera for {channel_key} is {round(updated_exposure_time*1000, 1)}ms, not {exposure_time*1000}ms!")
                        exposure_time = round(updated_exposure_time, 4)
                        # update the experiment file
                        channel["camera_exposure_time"] = round(updated_exposure_time * 1000, 1)
                        self.output_event_queue.put(("exposure_time", (channel_key, channel["camera_exposure_time"])))

                sweep_time = (
                    exposure_time
                    + readout_time
                    + camera_delay
                    + max(remote_focus_ramp_falling + duty_cycle_wait_duration, camera_settle_duration, camera_delay) - camera_delay
                )        
                # TODO: should we keep the percent_smoothing?
                if ps > 0:
                    sweep_time = (1 + ps / 100) * sweep_time

                exposure_times[channel_key] = exposure_time + readout_time
                sweep_times[channel_key] = sweep_time

        return exposure_times, sweep_times
