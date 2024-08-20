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

# Standard Library imports
import logging
import importlib  # noqa: F401
from multiprocessing.managers import ListProxy

from navigate.model.device_startup_functions import (
    start_stage,
)
from navigate.tools.common_functions import build_ref_name

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Microscope:
    """Microscope Class - Used to control the microscope."""

    def __init__(
        self, name, configuration, devices_dict, is_synthetic=False, is_virtual=False
    ):
        """Initialize the microscope.

        Parameters
        ----------
        name : str
            Name of the microscope.
        configuration : dict
            Configuration dictionary.
        devices_dict : dict
            Dictionary of devices.
        is_synthetic : bool, optional
            Is synthetic, by default False
        is_virtual : bool, optional
            Is virtual, by default False
        """

        # Initialize microscope object
        #: str: Name of the microscope.
        self.microscope_name = name

        #: dict: Configuration dictionary.
        self.configuration = configuration

        #: SharedNDArray: Buffer for image data.
        self.data_buffer = None

        #: dict: Dictionary of stages.
        self.stages = {}

        #: list: List of stages.
        self.stages_list = []

        #: bool: Ask stage for position.
        self.ask_stage_for_position = True

        #: dict: Dictionary of lasers.
        self.lasers = {}

        #: dict: Dictionary of galvanometers.
        self.galvo = {}

        #: dict: Dictionary of filter_wheels
        self.filter_wheel = {}

        #: dict: Dictionary of data acquisition devices.
        self.daq = devices_dict.get("daq", None)

        #: dict: Dictionary of microscope info.
        self.info = {}

        #: int: Current channel.
        self.current_channel = None

        #: int: Current laser index.
        self.current_laser_index = 0

        #: list: List of all channels.
        self.channels = None

        #: list: List of available channels.
        self.available_channels = None

        #: int: Number of images.
        self.number_of_frames = None

        #: float: Central focus position.
        self.central_focus = None

        #: Bool: Is a synthetic microscope.
        self.is_synthetic = is_synthetic

        #: list: List of laser wavelengths.
        self.laser_wavelength = []

        #: dict: Dictionary of returned stage positions.
        self.ret_pos_dict = {}

        #: dict: Dictionary of commands
        self.commands = {}

        #: dict: Dictionary of plugin devices
        self.plugin_devices = {}

        if is_virtual:
            return

        device_ref_dict = {
            "camera": ["serial_number"],
            "filter_wheel": ["type", "wheel_number"],
            "zoom": ["type", "servo_id"],
            "shutter": ["type", "channel"],
            "remote_focus_device": ["type", "channel"],
            "galvo": ["type", "channel"],
            "lasers": ["wavelength"],
            "mirror": ["type"],
        }

        device_name_dict = {"lasers": "wavelength"}

        laser_list = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["lasers"]

        #: dict: Dictionary of laser configurations.
        self.laser_wavelength = [laser["wavelength"] for laser in laser_list]

        if "__plugins__" not in devices_dict:
            devices_dict["__plugins__"] = {}

        # Load and start all devices
        for device_name in self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ].keys():

            # Skip the daq and stage devices. These are handled separately.
            if device_name in ["daq", "stage"]:
                continue
            is_plugin = False
            device_connection = None
            (
                device_config_list,
                device_name_list,
                is_list,
            ) = self.assemble_device_config_lists(
                device_name=device_name, device_name_dict=device_name_dict
            )
            if device_name not in device_ref_dict:
                if device_name in devices_dict["__plugins__"]:
                    device_ref_dict[device_name] = devices_dict["__plugins__"][
                        device_name
                    ]["ref_list"]
                    is_plugin = True
                else:
                    print(
                        f"Device {device_name} could not be loaded! "
                        f"Please make sure there is no spelling error!"
                    )
                    logger.debug(
                        f"Device {device_name} could not be loaded! "
                        f"Please make sure there is no spelling error!"
                    )
                    continue
            for i, device in enumerate(device_config_list):
                device_ref_name = None
                if "hardware" in device.keys():
                    ref_list = [
                        device["hardware"][k] for k in device_ref_dict[device_name]
                    ]

                else:
                    try:
                        ref_list = [device[k] for k in device_ref_dict[device_name]]
                    except KeyError:
                        ref_list = []

                device_ref_name = build_ref_name("_", *ref_list)
                if (
                    device_name in devices_dict
                    and device_ref_name in devices_dict[device_name]
                ):
                    device_connection = devices_dict[device_name][device_ref_name]

                elif is_plugin:
                    device_plugin_dict = devices_dict.get(device_name, {})
                    try:
                        exec(
                            f"device_plugin_dict['{device_ref_name}'] = devices_dict["
                            f"'__plugins__']['{device_name}']['load_device']"
                            f"(configuration['configuration']['microscopes']["
                            f"self.microscope_name]['{device_name}']['hardware'], "
                            f"is_synthetic)"
                        )
                        devices_dict[device_name] = device_plugin_dict
                        device_connection = device_plugin_dict[device_ref_name]
                        exec(
                            f"self.plugin_devices['{device_name}'] = devices_dict["
                            f"'__plugins__']['{device_name}']['start_device']"
                            f"(self.microscope_name, device_connection, configuration, "
                            f"is_synthetic)"
                        )
                    except RuntimeError:
                        print(
                            f"Device {device_name} isn't loaded correctly! "
                            f"Please check the spelling and the plugin!"
                        )
                        continue

                    self.info[device_name] = device_ref_name
                    commands_dict = self.plugin_devices[device_name].commands
                    for command in commands_dict:
                        self.commands[command] = (device_name, commands_dict[command])
                    continue

                # SHARED DEVICES
                elif device_ref_name.startswith("NI") and (
                    device_name == "galvo" or device_name == "remote_focus_device"
                ):
                    device_connection = self.daq

                if device_ref_name.startswith("EquipmentSolutions"):
                    device_connection = self.daq

                # LOAD AND START DEVICES
                self.load_and_start_devices(
                    device_name=device_name,
                    is_list=is_list,
                    device_name_list=device_name_list,
                    device_ref_name=device_ref_name,
                    device_connection=device_connection,
                    name=name,
                    i=i,
                    plugin_devices=devices_dict["__plugins__"],
                )

                if device_connection is None and device_ref_name is not None:
                    if device_name not in devices_dict:
                        devices_dict[device_name] = {}

                    devices_dict[device_name][device_ref_name] = (
                        getattr(self, device_name)[device_name_list[i]]
                        if is_list
                        else getattr(self, device_name)
                    )

        # stages
        stage_devices = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["stage"]["hardware"]

        # set the NI Galvo stage flag
        self.configuration["configuration"]["microscopes"][self.microscope_name][
            "stage"
        ]["has_ni_galvo_stage"] = False
        if type(stage_devices) != ListProxy:
            stage_devices = [stage_devices]

        for i, device_config in enumerate(stage_devices):
            device_ref_name = build_ref_name(
                "_", device_config["type"], device_config["serial_number"]
            )

            if device_ref_name not in devices_dict["stages"]:
                logger.debug(f"{device_ref_name} stage not found in the devices_dict!")
                raise Exception(
                    "Stage not found. "
                    "This often arises when the configuration.yaml file is "
                    "incorrectly specified. Please check the "
                    "configuration.yaml file and try again. Things to "
                    "check include: ",
                    "1. If no stage is physically connected to the "
                    "microscope, one must still be listed in the "
                    "configuration.yaml file. We recommend that you use a"
                    "`SyntheticStage`. "
                    "2. If a stage is physically connected to the "
                    "microscope, make sure that it is corrected defined in "
                    "both the `hardware` and `microscopes` sections of the "
                    "configuration.yaml file. Importantly, name, "
                    "type, and serial numbers must match. "
                    "3. You may be using a stage that is not supported by "
                    "Navigate. Please check the list of supported stages in "
                    "the documentation."
                    f"The stage that failed to load is: {device_ref_name}",
                )

            # SHARED DEVICES
            if device_ref_name.startswith("GalvoNIStage"):
                devices_dict["stages"][device_ref_name] = self.daq
                # set the NI Galvo stage flag
                self.configuration["configuration"]["microscopes"][
                    self.microscope_name
                ]["stage"]["has_ni_galvo_stage"] = True

            stage = start_stage(
                microscope_name=self.microscope_name,
                device_connection=devices_dict["stages"][device_ref_name],
                configuration=self.configuration,
                id=i,
                is_synthetic=is_synthetic,
                plugin_devices=devices_dict["__plugins__"],
            )
            for axis in device_config["axes"]:
                self.stages[axis] = stage
                self.info[f"stage_{axis}"] = device_ref_name

            self.stages_list.append((stage, list(device_config["axes"])))

        # connect daq and camera in synthetic mode
        if is_synthetic:
            self.daq.add_camera(self.microscope_name, self.camera)

    def update_data_buffer(self, data_buffer, number_of_frames):
        """Update the data buffer for the camera.

        Parameters
        ----------
        data_buffer : numpy.ndarray
            Data buffer for the camera.
        number_of_frames : int
            Number of frames to be acquired.
        """

        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.data_buffer = data_buffer
        self.number_of_frames = number_of_frames

    def move_stage_offset(self, former_microscope=None):
        """Move the stage to the offset position.

        Parameters
        ----------
        former_microscope : str
            Name of the former microscope.
        """

        if former_microscope:
            former_offset_dict = self.configuration["configuration"]["microscopes"][
                former_microscope
            ]["stage"]
        else:
            former_offset_dict = dict((f"{a}_offset", 0) for a in self.stages)
        self_offset_dict = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["stage"]
        self.ask_stage_for_position = True
        # print(self.stages)
        pos_dict = self.get_stage_position()
        for stage, axes in self.stages_list:

            # x_abs: current x_pos + current_x_offset - former_x_offset
            pos = {
                axis
                + "_abs": (
                    pos_dict[axis + "_pos"]
                    + self_offset_dict[axis + "_offset"]
                    - former_offset_dict[axis + "_offset"]
                )
                for axis in axes
            }
            stage.move_absolute(pos, wait_until_done=True)
        self.ask_stage_for_position = True

    def prepare_acquisition(self):
        """Prepare the acquisition.

        Returns
        -------
        waveform : dict
            Dictionary of all the waveforms.
        """
        self.current_channel = 0
        self.central_focus = None
        self.channels = self.configuration["experiment"]["MicroscopeState"]["channels"]
        self.available_channels = list(
            map(
                lambda c: int(c[len("channel_") :]),
                filter(lambda k: self.channels[k]["is_selected"], self.channels.keys()),
            )
        )
        if self.camera.is_acquiring:
            self.camera.close_image_series()

        # set ROI
        img_width = self.configuration["experiment"]["CameraParameters"]["x_pixels"]
        img_height = self.configuration["experiment"]["CameraParameters"]["y_pixels"]
        center_x = self.configuration["experiment"]["CameraParameters"]["center_x"]
        center_y = self.configuration["experiment"]["CameraParameters"]["center_y"]
        self.camera.set_ROI(img_width, img_height, center_x, center_y)

        # Set Camera Sensor Mode - Must be done before camera is initialized.
        sensor_mode = self.configuration["experiment"]["CameraParameters"][
            "sensor_mode"
        ]

        self.camera.set_sensor_mode(sensor_mode)
        if sensor_mode == "Light-Sheet":
            self.camera.set_readout_direction(
                self.configuration["experiment"]["CameraParameters"][
                    "readout_direction"
                ]
            )

        # set binning
        self.camera.set_binning(
            self.configuration["experiment"]["CameraParameters"]["binning"]
        )
        # Initialize Image Series - Attaches camera buffer and start imaging
        self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)

        # calculate all the waveform
        self.shutter.open_shutter()

        return self.calculate_all_waveform()

    def end_acquisition(self):
        """End the acquisition."""
        self.daq.stop_acquisition()
        self.stop_stage()
        if self.central_focus is not None:
            self.move_stage({"f_abs": self.central_focus})
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.shutter.close_shutter()
        for k in self.lasers:
            self.lasers[k].turn_off()
        self.current_channel = 0
        self.central_focus = None

    def turn_on_laser(self):
        """Turn on the current laser."""
        self.lasers[str(self.laser_wavelength[self.current_laser_index])].turn_on()

    def turn_off_lasers(self):
        """Turn off current laser."""
        self.lasers[str(self.laser_wavelength[self.current_laser_index])].turn_off()

    def calculate_all_waveform(self):
        """Calculate all the waveforms.

        Returns
        -------
        waveform : dict
            Dictionary of all the waveforms.
        """
        exposure_times, sweep_times = self.calculate_exposure_sweep_times()
        camera_waveform = self.daq.calculate_all_waveforms(
            self.microscope_name, exposure_times, sweep_times
        )
        remote_focus_waveform = self.remote_focus_device.adjust(
            exposure_times, sweep_times
        )
        galvo_waveform = [
            self.galvo[k].adjust(exposure_times, sweep_times) for k in self.galvo
        ]

        # calculate waveform for galvo stage
        for stage, _ in self.stages_list:
            if type(stage).__name__ == "GalvoNIStage":
                stage.switch_mode("normal", exposure_times, sweep_times)
        waveform_dict = {
            "camera_waveform": camera_waveform,
            "remote_focus_waveform": remote_focus_waveform,
            "galvo_waveform": galvo_waveform,
        }
        return waveform_dict

    def calculate_exposure_sweep_times(self):
        """Calculate the exposure and sweep times for all channels.

        The `calculate_exposure_sweep_times` function calculates and returns exposure
        times and sweep times for all channels in a microscope configuration. It takes
        the camera's readout time as an input parameter and considers various parameters
        such as camera exposure time, delay percentages, and smoothing to compute these
        times. The function iterates through the channels, performs calculations, and
        returns the results as dictionaries containing exposure times and sweep times
        for each channel.

        Returns
        -------
        exposure_times : dict
            Dictionary of exposure times.
        sweep_times : dict
            Dictionary of sweep times.

        """
        exposure_times = {}
        sweep_times = {}
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        # zoom = microscope_state["zoom"] # assigned but not used?
        waveform_constants = self.configuration["waveform_constants"]
        camera_delay = (
            self.configuration["configuration"]["microscopes"][self.microscope_name][
                "camera"
            ]["delay"]
            / 1000
        )
        camera_settle_duration = (
            self.configuration["configuration"]["microscopes"][self.microscope_name][
                "camera"
            ].get("settle_duration", 0)
            / 1000
        )
        remote_focus_ramp_falling = (
            float(waveform_constants["other_constants"]["remote_focus_ramp_falling"])
            / 1000
        )

        duty_cycle_wait_duration = (
            float(waveform_constants["other_constants"]["remote_focus_settle_duration"])
            / 1000
        )
        ps = float(waveform_constants["other_constants"].get("percent_smoothing", 0.0))

        readout_time = 0
        readout_mode = self.configuration["experiment"]["CameraParameters"][
            "sensor_mode"
        ]
        if readout_mode == "Normal":
            readout_time = self.camera.calculate_readout_time()
        elif self.configuration["experiment"]["CameraParameters"][
            "readout_direction"
        ] in ["Bidirectional", "Rev. Bidirectional"]:
            remote_focus_ramp_falling = 0
        # set readout out time
        self.configuration["experiment"]["CameraParameters"]["readout_time"] = (
            readout_time * 1000
        )

        for channel_key in microscope_state["channels"].keys():
            channel = microscope_state["channels"][channel_key]
            if channel["is_selected"] is True:
                exposure_time = float(channel["camera_exposure_time"]) / 1000

                if readout_mode == "Light-Sheet":
                    (
                        _,
                        _,
                        updated_exposure_time,
                    ) = self.camera.calculate_light_sheet_exposure_time(
                        exposure_time,
                        int(
                            self.configuration["experiment"]["CameraParameters"][
                                "number_of_pixels"
                            ]
                        ),
                    )
                    if updated_exposure_time != exposure_time:
                        print(
                            f"*** Notice: The actual exposure time of the camera for "
                            f"{channel_key} is {round(updated_exposure_time*1000, 1)}"
                            f"ms, not {exposure_time*1000}ms!"
                        )
                        exposure_time = round(updated_exposure_time, 4)
                        # update the experiment file
                        channel["camera_exposure_time"] = round(
                            updated_exposure_time * 1000, 1
                        )
                        self.output_event_queue.put(
                            (
                                "exposure_time",
                                (channel_key, channel["camera_exposure_time"]),
                            )
                        )

                sweep_time = (
                    exposure_time
                    + readout_time
                    + camera_delay
                    + max(
                        remote_focus_ramp_falling + duty_cycle_wait_duration,
                        camera_settle_duration,
                        camera_delay,
                    )
                    - camera_delay
                )
                # TODO: should we keep the percent_smoothing?
                if ps > 0:
                    sweep_time = (1 + ps / 100) * sweep_time

                exposure_times[channel_key] = exposure_time + readout_time
                sweep_times[channel_key] = sweep_time

        self.exposure_times = exposure_times
        self.sweep_times = sweep_times

        return exposure_times, sweep_times

    def get_exposure_sweep_times(self):
        """Get the exposure and sweep times for all channels.

        Returns
        -------
        exposure_times : dict
            Dictionary of exposure times.
        sweep_times : dict
            Dictionary of sweep times.

        """
        return self.exposure_times, self.sweep_times

    def prepare_next_channel(self, update_daq_task_flag=True):
        """Prepare the next channel.

        This function, `prepare_next_channel`, is responsible for configuring various
        hardware components for the next imaging channel in an experimental setup.
        It sequentially selects the next available channel, sets the filter wheel,
        camera exposure time, laser power, and other parameters based on the selected
        channel's configuration. Additionally, it stops data acquisition, prepares the
        data acquisition system for the new channel, and adjusts the focus position as
        necessary, ensuring the hardware is ready for imaging the selected channel.

        Parameters
        ----------
        update_daq_task_flag : bool
            whether to override waveforms in the DAQ (create new tasks)
        """
        curr_channel = self.current_channel
        prefix = "channel_"
        if self.current_channel == 0:
            self.current_channel = self.available_channels[0]
        else:
            idx = (self.available_channels.index(self.current_channel) + 1) % len(
                self.available_channels
            )
            self.current_channel = self.available_channels[idx]
        if curr_channel == self.current_channel:
            return

        channel_key = prefix + str(self.current_channel)
        channel = self.configuration["experiment"]["MicroscopeState"]["channels"][
            channel_key
        ]
        # Filter Wheel Settings.
        for k in self.filter_wheel:
            self.filter_wheel[k].set_filter(channel[k])

        # Camera Settings
        self.current_exposure_time = float(channel["camera_exposure_time"]) / 1000
        if (
            self.configuration["experiment"]["CameraParameters"]["sensor_mode"]
            == "Light-Sheet"
        ):
            (
                self.current_exposure_time,
                camera_line_interval,
                _,
            ) = self.camera.calculate_light_sheet_exposure_time(
                self.current_exposure_time,
                int(
                    self.configuration["experiment"]["CameraParameters"][
                        "number_of_pixels"
                    ]
                ),
            )
            self.camera.set_line_interval(camera_line_interval)
        self.camera.set_exposure_time(self.current_exposure_time)

        # Laser Settings
        self.current_laser_index = channel["laser_index"]
        for k in self.lasers:
            self.lasers[k].turn_off()
        self.lasers[str(self.laser_wavelength[self.current_laser_index])].set_power(
            channel["laser_power"]
        )
        # self.lasers[str(self.laser_wavelength[self.current_laser_index])].turn_on()

        # stop daq before writing new waveform
        # When called the first time, throws an error.
        # choose to not update the waveform is very useful when running ZStack
        # if there is a NI Galvo stage in the system.
        if update_daq_task_flag:
            self.daq.stop_acquisition()
            self.daq.prepare_acquisition(channel_key)

        # Add Defocus term
        # Assume wherever we start is the central focus
        # TODO: is this the correct assumption?
        if self.central_focus is None:
            self.central_focus = self.get_stage_position().get("f_pos")
        if self.central_focus is not None:
            self.move_stage(
                {"f_abs": self.central_focus + float(channel["defocus"])},
                wait_until_done=True,
                update_focus=False,
            )

    def move_stage(self, pos_dict, wait_until_done=False, update_focus=True):
        """Move stage to a position.

        Parameters
        ----------
        pos_dict : dict
            Dictionary of stage positions.
        wait_until_done : bool, optional
            Wait until stage is done moving, by default False
        update_focus : bool, optional
            Update the central focus

        Returns
        -------
        success : bool
            True if stage is successfully moved, False otherwise.
        """
        self.ask_stage_for_position = True

        if len(pos_dict.keys()) == 1:
            axis_key = list(pos_dict.keys())[0]
            axis = axis_key[: axis_key.index("_")]
            if update_focus and axis == "f":
                self.central_focus = None
            return self.stages[axis].move_axis_absolute(
                axis, pos_dict[axis_key], wait_until_done
            )

        success = True
        for stage, axes in self.stages_list:
            pos = {
                axis: pos_dict[axis]
                for axis in pos_dict
                if axis[: axis.index("_")] in axes
            }
            if pos:
                success = stage.move_absolute(pos, wait_until_done) and success

        if update_focus and "f_abs" in pos_dict:
            self.central_focus = None

        return success

    def stop_stage(self):
        """Stop stage."""

        self.ask_stage_for_position = True

        for stage, axes in self.stages_list:
            stage.stop()

        self.central_focus = self.get_stage_position().get("f_pos", self.central_focus)

    def get_stage_position(self):
        """Get stage position.

        Returns
        -------
        stage_position : dict
            Dictionary of stage positions.
        """
        if self.ask_stage_for_position:
            # self.ret_pos_dict = {}
            for stage, axes in self.stages_list:
                temp_pos = stage.report_position()
                self.ret_pos_dict.update(temp_pos)
            self.ask_stage_for_position = False
        return self.ret_pos_dict

    def move_remote_focus(self, offset=None):
        """Move remote focus.

        Parameters
        ----------
        offset : float, optional
            Offset, by default None
        """
        exposure_times, sweep_times = self.calculate_exposure_sweep_times()
        self.remote_focus_device.move(exposure_times, sweep_times, offset)

    def update_stage_limits(self, limits_flag=True):
        """Update stage limits.

        Parameters
        ----------
        limits_flag : bool, optional
            Limits flag, by default True
        """
        self.ask_stage_for_position = True
        for stage, _ in self.stages_list:
            stage.stage_limits = limits_flag

    def assemble_device_config_lists(self, device_name, device_name_dict):
        """Assemble device config lists.

        Parameters
        ----------
        device_name : str
            Device name.
        device_name_dict : dict
            Device name dictionary.

        Returns
        -------
        device_config_list : list
            Device configuration list.
        device_name_list : list
            Device name list.
        """
        device_config_list = []
        device_name_list = []

        try:
            devices = self.configuration["configuration"]["microscopes"][
                self.microscope_name
            ][device_name]
        except KeyError:
            # if no such device
            return [], [], False

        if type(devices) == ListProxy:
            i = 0
            for d in devices:
                device_config_list.append(d)
                if device_name in device_name_dict:
                    device_name_list.append(
                        build_ref_name("_", d[device_name_dict[device_name]])
                    )

                else:
                    device_name_list.append(build_ref_name("_", device_name, i))
                i += 1
            is_list = True

        else:
            device_config_list.append(devices)
            is_list = False

        return device_config_list, device_name_list, is_list

    def load_and_start_devices(
        self,
        device_name,
        is_list,
        device_name_list,
        device_ref_name,
        device_connection,
        name,
        i,
        plugin_devices,
    ):
        """Load and start devices.

        Parameters
        ----------
        device_name : str
            Device name.
        is_list : bool
            Is list.
        device_name_list : list
            Device name list.
        device_ref_name : str
            Device reference name.
        device_connection : str
            Device connection.
        name : str
            Name.
        i : int
            Index.
        plugin_devices : dict
            Plugin Devices
        """
        # Import start_device classes
        try:
            exec(
                f"start_{device_name}=importlib.import_module("
                f"'navigate.model.device_startup_functions').start_{device_name}"
            )
        except AttributeError:
            print(f"Could not import start_{device_name}")
            print(f"Could not load device {device_name}")

        # Start the devices
        if is_list:
            exec(
                f"self.{device_name}['{device_name_list[i]}'] = "
                f"start_{device_name}(name, device_connection, self.configuration, "
                f"i, self.is_synthetic, plugin_devices)"
            )
            if device_name in device_name_list[i]:
                self.info[device_name_list[i]] = device_ref_name
        else:
            exec(
                f"self.{device_name} = start_{device_name}(name, "
                f"device_connection, self.configuration, "
                f"self.is_synthetic, plugin_devices)"
            )
            self.info[device_name] = device_ref_name

    def terminate(self):
        """Close hardware explicitly.

        Should close camera, filter_wheel, zoom, shutter,
        remote_focus_device, galvo, lasers, stages, daq.

        TODO: Zoom and Mirror devices are not called.
        """
        self.camera.__del__()

        for k in self.filter_wheel:
            self.filter_wheel[k].__del__()

        self.shutter.__del__()

        try:
            self.remote_focus_device.__del__()
        except Exception as e:
            logger.debug(f"Remote focus delete failure: {e}")

        for k in self.galvo:
            self.galvo[k].__del__()

        for k in self.lasers:
            self.lasers[k].__del__()

        for stage, _ in self.stages_list:
            try:
                stage.close()
            except Exception as e:
                logger.debug(f"Stage delete failure: {e}")

        self.daq.__del__()

    def run_command(self, command, *args):
        if command in self.commands:
            result = self.commands[command][1](*args)
            if result:
                device_name = self.commands[command][0]
                self.output_event_queue.put((device_name, result))
        else:
            print("unknown command in the Microscope:", command)
