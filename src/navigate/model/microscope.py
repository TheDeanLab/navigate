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

# Standard Library imports
import logging
import importlib  # noqa: F401
from multiprocessing.managers import ListProxy
import reprlib
from typing import Any, Dict, List, Optional

# Third-party imports
import numpy as np

# Local application imports
from navigate.model.device_startup_functions import load_devices, start_device
from navigate.tools.common_functions import build_ref_name

# Set up logging
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Microscope:
    """Microscope Class - Used to control the microscope."""

    def __init__(
        self,
        name: str,
        configuration: Dict[str, Any],
        devices_dict: dict,
        is_synthetic: bool = False,
        is_virtual: bool = False,
    ) -> None:
        """Initialize the microscope.

        Parameters
        ----------
        name : str
            Name of the microscope.
        configuration : Dict[str, Any]
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

        #: Queue: Output event queue.
        self.output_event_queue = None

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

        #: obj: Camera object.
        self.camera = None

        #: Any: Shutter device.
        self.shutter = None

        #: dict: Dictionary of lasers.
        self.laser = {}

        #: dict: Dictionary of galvanometers.
        self.galvo = {}

        #: Any: Remote focus device.
        self.remote_focus = None

        #: dict: Dictionary of filter_wheels
        self.filter_wheel = {}

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
            "remote_focus": ["type", "channel"],
            "galvo": ["type", "channel"],
            "laser": ["wavelength"],
            "mirror": ["type"],
        }

        device_name_dict = {"laser": "wavelength"}

        laser_list = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["laser"]

        #: dict: Dictionary of laser configurations.
        self.laser_wavelength = [laser["wavelength"] for laser in laser_list]

        if "__plugins__" not in devices_dict:
            devices_dict["__plugins__"] = {}

        devices_dict = load_devices(
            self.microscope_name,
            configuration,
            is_synthetic,
            devices_dict,
            devices_dict["__plugins__"],
        )
        daq_type = (
            "Synthetic"
            if is_synthetic
            else self.configuration["configuration"]["microscopes"][
                self.microscope_name
            ]["daq"]["hardware"]["type"]
        )
        #: dict: Dictionary of data acquisition devices.
        self.daq = devices_dict["daq"].get(daq_type, None)

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
            # new device type
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
                try:
                    ref_list = [
                        device["hardware"][k] for k in device_ref_dict[device_name]
                    ]
                except Exception as e:
                    logger.error(
                        f"Can't get the device attributes in configuration file: {e}"
                    )

                device_ref_name = build_ref_name("_", *ref_list)
                if (
                    device_name in devices_dict
                    and device_ref_name in devices_dict[device_name]
                ):
                    # get the device
                    device_connection = devices_dict[device_name][device_ref_name]

                if is_plugin:
                    device_plugin_dict = devices_dict.get(device_name, {})
                    try:
                        if device_connection is None:
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
            if device_config["type"] == "NIStage":
                self.configuration["configuration"]["microscopes"][
                    self.microscope_name
                ]["stage"]["has_ni_galvo_stage"] = True

            try:
                stage = start_device(
                    microscope_name=self.microscope_name,
                    configuration=self.configuration,
                    device_category="stage",
                    device_id=i,
                    is_synthetic=is_synthetic,
                    daq_connection=self.daq,
                    plugin_devices=devices_dict["__plugins__"],
                )
            except Exception as e:
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
            for axis in device_config["axes"]:
                self.stages[axis] = stage
                self.info[f"stage_{axis}"] = device_ref_name

            self.stages_list.append((stage, list(device_config["axes"])))

        # connect daq and camera in synthetic mode
        if is_synthetic and self.daq is not None:
            self.daq.add_camera(self.microscope_name, self.camera)

    def update_data_buffer(
        self, data_buffer: List[np.ndarray], number_of_frames: int
    ) -> None:
        """Update the data buffer for the camera.

        Parameters
        ----------
        data_buffer : List[np.ndarray]
            Data buffer for the camera.
        number_of_frames : int
            Number of frames to be acquired.
        """

        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.data_buffer = data_buffer
        self.number_of_frames = number_of_frames

    def move_stage_offset(self, former_microscope: Optional[str] = None) -> None:
        """Move the stage to the offset position.

        Parameters
        ----------
        former_microscope : Optional[str], optional
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
        pos_dict = self.get_stage_position()
        for stage, axes in self.stages_list:

            # x_abs: current x_pos + current_x_offset - former_x_offset
            pos = {
                axis
                + "_abs": (
                    pos_dict[axis + "_pos"]
                    + self_offset_dict.get(axis + "_offset", 0)
                    - former_offset_dict.get(axis + "_offset", 0)
                )
                for axis in axes
            }
            stage.move_absolute(pos, wait_until_done=True)
        self.ask_stage_for_position = True

    def prepare_acquisition(self) -> dict:
        """Prepare the acquisition.

        This function prepares the acquisition by identifying which channels are
        selected for imaging, setting the camera region of interest (ROI), setting
        the camera sensor mode, setting the camera binning, initializing the image
        series, calculating all the waveforms required for the acquisition process,
        and opens the shutter.

        Returns
        -------
        waveform : dict/None
            Dictionary of all the waveforms. None if the camera ROI and binning are
            not set successfully.
        """
        self.current_channel = 0
        self.central_focus = None
        self.get_available_channels()

        if self.camera.is_acquiring:
            self.camera.close_image_series()
        # set camera trigger source
        self.set_camera_trigger_mode()
        self.set_camera_sensor_mode()
        if not self.set_camera_roi_and_binning():
            return None
        logger.debug(f"Running microscope {self.microscope_name}")
        self.report_camera_settings()
        # Initialize Image Series - Attaches camera buffer and start imaging
        self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)

        # calculate all the waveform
        self.shutter.open_shutter()

        return self.calculate_all_waveform()

    def get_available_channels(self) -> None:
        """Get the available channels for imaging.

        This function gets the available channels for imaging by identifying which
        channels are selected for imaging in the configuration file.
        """
        self.channels = self.configuration["experiment"]["MicroscopeState"]["channels"]
        self.available_channels = list(
            map(
                lambda c: int(c[len("channel_") :]),
                filter(lambda k: self.channels[k]["is_selected"], self.channels.keys()),
            )
        )

    def report_camera_settings(self) -> None:
        """Log the camera settings.

        This function logs the camera settings for the current acquisition. It logs the
        camera parameters specified in the configuration file for the current
        microscope.
        """
        camera_info = reprlib.Repr()
        camera_info.indent = "---"
        camera_info.maxdict = 20
        camera_info = camera_info.repr(
            dict(
                self.configuration["experiment"]["CameraParameters"][
                    self.microscope_name
                ]
            )
        )
        logger.info(f"Preparing Acquisition. Camera Parameters: {camera_info}")

    def set_camera_trigger_mode(self) -> None:
        """Set the camera trigger mode.

        This function sets the camera trigger source, trigger mode."""
        trigger_source = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ].get("trigger_source", "External")
        self.camera.set_trigger_mode(trigger_source)

    def set_camera_sensor_mode(self) -> None:
        """Set the camera sensor mode.

        This function sets the camera sensor mode based on the camera parameters
        specified in the configuration file. It sets the sensor mode and the readout
        direction for the camera if it is in the light-sheet imaging mode.
        """
        # Set Camera Sensor Mode - Must be done before camera is initialized.
        sensor_mode = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["sensor_mode"]
        self.camera.set_sensor_mode(sensor_mode)
        if sensor_mode == "Light-Sheet":
            self.camera.set_readout_direction(
                self.configuration["experiment"]["CameraParameters"][
                    self.microscope_name
                ]["readout_direction"]
            )

    def set_camera_roi_and_binning(self) -> bool:
        """Set the camera ROI and binning.

        This function sets the camera region of interest (ROI) based on the camera
        parameters specified in the configuration file. It sets the image width,
        image height, and the center of the image. The camera ROI is used to define
        the area of the image sensor that will be used to capture images during the
        acquisition process. The function also sets the camera binning value.

        Returns
        -------
        bool
            True if the camera ROI and binning are set successfully, False otherwise.
        """

        img_width = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["x_pixels"]
        img_height = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["y_pixels"]
        center_x = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["center_x"]
        center_y = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["center_y"]
        self.camera.set_ROI(img_width, img_height, center_x, center_y)
        return self.camera.set_ROI_and_binning(
            img_width,
            img_height,
            center_x,
            center_y,
            self.configuration["experiment"]["CameraParameters"][self.microscope_name][
                "binning"
            ],
        )

    def end_acquisition(self) -> None:
        """End the acquisition.

        This function stops the acquisition, which includes stopping the data
        acquisition system, closing the camera image series, closing the shutter,
        turning off the lasers, and moving the stage to the central focus
        position if it was moved during the acquisition. It also stops the stage if
        it is moving.

        For ASI daq systems, it also stops the ASI galvos (TG-1000 waveforms in SAM mode
        4 must be manually shut off).
        """
        self.daq.stop_acquisition()
        galvo_type = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["galvo"][0]["hardware"]["type"]
        if galvo_type == "asi.ASI":
            for k in self.galvo:
                self.galvo[k].turn_off()

        self.stop_stage()
        if self.central_focus is not None:
            self.move_stage({"f_abs": self.central_focus})
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.shutter.close_shutter()
        for k in self.laser:
            self.laser[k].turn_off()
        self.current_channel = 0
        self.central_focus = None
        logger.info("Acquisition Ended")

    def turn_on_laser(self) -> None:
        """Turn on the current laser."""
        logger.info(
            f"Turning on laser {self.laser_wavelength[self.current_laser_index]}"
        )
        self.laser[str(self.laser_wavelength[self.current_laser_index])].turn_on()

    def turn_off_lasers(self) -> None:
        """Turn off current laser."""
        logger.info(
            f"Turning off laser {self.laser_wavelength[self.current_laser_index]}"
        )
        self.laser[str(self.laser_wavelength[self.current_laser_index])].turn_off()

    def calculate_all_waveform(self) -> dict:
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
        remote_focus_waveform = self.remote_focus.adjust(exposure_times, sweep_times)
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

    def calculate_exposure_sweep_times(self) -> tuple:
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
        waveform_constants = self.configuration["waveform_constants"]

        logger.info(f"Microscope state: {repr(dict(microscope_state))}")
        logger.info(f"Waveform constants: {repr(dict(waveform_constants))}")

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
            self.microscope_name
        ]["sensor_mode"]

        if readout_mode == "Normal":
            readout_time = self.camera.calculate_readout_time()
        elif self.configuration["experiment"]["CameraParameters"][self.microscope_name][
            "readout_direction"
        ] in ["Bidirectional", "Rev. Bidirectional"]:
            remote_focus_ramp_falling = 0
        # set readout out time
        self.configuration["experiment"]["CameraParameters"][self.microscope_name][
            "readout_time"
        ] = (readout_time * 1000)

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
                                self.microscope_name
                            ]["number_of_pixels"]
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

    def get_exposure_sweep_times(self) -> tuple:
        """Get the exposure and sweep times for all channels.

        Returns
        -------
        exposure_times : dict
            Dictionary of exposure times.
        sweep_times : dict
            Dictionary of sweep times.

        """
        return self.exposure_times, self.sweep_times

    def prepare_next_channel(self, update_daq_task_flag: bool = True) -> None:
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
        if self.current_channel == 0:
            self.current_channel = self.available_channels[0]
        else:
            idx = (self.available_channels.index(self.current_channel) + 1) % len(
                self.available_channels
            )
            self.current_channel = self.available_channels[idx]
        if curr_channel == self.current_channel:
            return

        prefix = "channel_"
        channel_key = prefix + str(self.current_channel)
        channel = self.configuration["experiment"]["MicroscopeState"]["channels"][
            channel_key
        ]
        # Filter Wheel Settings.
        for k in self.filter_wheel:
            self.filter_wheel[k].set_filter(channel[k])

        # Camera Settings
        self.set_camera_exposure_time(channel)

        # Laser Settings
        self.current_laser_index = channel["laser_index"]
        for k in self.laser:
            self.laser[k].turn_off()
        self.laser[str(self.laser_wavelength[self.current_laser_index])].set_power(
            channel["laser_power"]
        )
        logger.info(
            f"{self.laser_wavelength[self.current_laser_index]} "
            f"nm laser power set to {channel['laser_power']}"
        )
        # self.laser[str(self.laser_wavelength[self.current_laser_index])].turn_on()

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

    def set_camera_exposure_time(self, channel: dict) -> None:
        """Set the camera exposure time.

        This function prepares the camera for imaging by setting the camera exposure
        time based on the selected channel's configuration. It also adjusts the
        camera line interval if the sensor mode is set to the Light-Sheet mode.

        Parameters
        ----------
        channel : dict
            Dictionary of channel parameters.
        """
        self.current_exposure_time = float(channel["camera_exposure_time"]) / 1000
        if (
            self.configuration["experiment"]["CameraParameters"][self.microscope_name][
                "sensor_mode"
            ]
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
                        self.microscope_name
                    ]["number_of_pixels"]
                ),
            )
            self.camera.set_line_interval(camera_line_interval)
            logger.info(f"Camera line interval set to {camera_line_interval}.")
        self.camera.set_exposure_time(self.current_exposure_time)
        logger.info(f"Camera exposure time set to {self.current_exposure_time}.")

    def move_stage(
        self, pos_dict: dict, wait_until_done: bool = False, update_focus: bool = True
    ) -> bool:
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

    def stop_stage(self) -> None:
        """Stop stage."""

        self.ask_stage_for_position = True

        for stage, axes in self.stages_list:
            stage.stop()

        self.central_focus = self.get_stage_position().get("f_pos", self.central_focus)

    def get_stage_position(self) -> dict:
        """Get stage position.

        Returns
        -------
        stage_position : dict
            Dictionary of stage positions.
        """
        if self.ask_stage_for_position:
            for stage, axes in self.stages_list:
                temp_pos = stage.report_position()
                self.ret_pos_dict.update(temp_pos)
            self.ask_stage_for_position = False
        return self.ret_pos_dict

    def move_remote_focus(self, offset: Optional[float] = None) -> None:
        """Move remote focus.

        Parameters
        ----------
        offset : Optional[float], optional
            Offset, by default None
        """
        exposure_times, sweep_times = self.calculate_exposure_sweep_times()
        self.remote_focus.move(exposure_times, sweep_times, offset)

    def update_stage_limits(self, limits_flag: bool = True) -> None:
        """Update stage limits.

        Parameters
        ----------
        limits_flag : bool, optional
            Limits flag, by default True
        """
        logger.info(f"Stage limits enabled: {limits_flag}")
        self.ask_stage_for_position = True
        for stage, _ in self.stages_list:
            stage.stage_limits = limits_flag

    def assemble_device_config_lists(
        self, device_name: str, device_name_dict: dict
    ) -> tuple:
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
        is_list : bool
            Is list.
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
        device_name: str,
        is_list: bool,
        device_name_list: list,
        device_ref_name: str,
        device_connection: Any,
        name: str,
        i: int,
        plugin_devices: dict,
    ) -> None:
        """Load and start devices.

        Function uses importlib to import the device startup functions and then
        starts the devices. If it is a list, it will start the device at the index i.
        If it is a plugin, it will load the plugin device.

        Parameters
        ----------
        device_name : str
            The name of the device.
        is_list : bool
            Whether the device is a list of devices.
        device_name_list : list
            The list of device names.
        device_ref_name : str
            The reference name of the device.
        device_connection : Any
            The communication instance of the device.
        name : str
            The name of the microscope.
        i : int
            Index.
        plugin_devices : dict
            Plugin Devices

        """

        # Start the devices
        if is_list:
            exec(
                f"self.{device_name}['{device_name_list[i]}'] = "
                f"start_device(name, self.configuration, '{device_name}', "
                f"i, self.is_synthetic, self.daq, plugin_devices)"
            )
            if device_name in device_name_list[i]:
                self.info[device_name_list[i]] = device_ref_name
        else:
            exec(
                f"self.{device_name} = start_device(name, "
                f"self.configuration, '{device_name}', 0, "
                f"self.is_synthetic, self.daq, plugin_devices)"
            )
            self.info[device_name] = device_ref_name

    def terminate(self) -> None:
        """Close hardware explicitly.

        Closes all devices other than plugin devices and deformable mirrors.
        """

        for device in [
            self.camera,
            self.daq,
            self.remote_focus,
            self.shutter,
            self.zoom,
        ]:
            del device

        for key in list(self.filter_wheel.keys()):
            del self.filter_wheel[key]

        for key in list(self.galvo.keys()):
            del self.galvo[key]

        for key in list(self.laser.keys()):
            del self.laser[key]

        for stage, _ in self.stages_list:
            del stage

    def run_command(self, command: str, *args) -> None:
        """Run command.

        Parameters
        ----------
        command : str
            Command.
        *args : list
            Variable input arguments.
        """
        logger.info(f"Running Command: {command}, {args}")
        if command in self.commands:
            result = self.commands[command][1](*args)
            if result:
                device_name = self.commands[command][0]
                self.output_event_queue.put((device_name, result))
        else:
            logger.debug(f"Unknown Command: {command}")
