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

from aslm.model.device_startup_functions import (
    start_stage,
)
from aslm.tools.common_functions import build_ref_name
from aslm.model.devices.stages.stage_galvo import GalvoNIStage
from aslm.controller.sub_controllers.waveform_popup_controller import WaveformPopupController
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Microscope:
    """Microscope Class

    This class is used to control the microscope.

    Attributes
    ----------
    configuration : dict
        Configuration dictionary.
    data_buffer : ListProxy
        Data buffer.
    daq : Daq
        Daq object.
    microscope_name : str
        Microscope name.
    number_of_frames : int
        Number of frames.

    Methods
    -------
    update_data_buffer(img_width, img_height, data_buffer, number_of_frames)
        Update the data buffer for the camera.
    move_stage_offset(former_microscope=None)
        Move the stage to the offset position.
    end_acquisition()
        End the acquisition.
    get_readout_time()
        Get readout time from camera.
    """

    def __init__(
        self, name, configuration, devices_dict, is_synthetic=False, is_virtual=False
    ):

        # Initialize microscope object
        self.microscope_name = name
        self.configuration = configuration
        self.data_buffer = None
        self.stages = {}
        self.stages_list = []
        self.ask_stage_for_position = True
        self.lasers = {}
        self.galvo = {}
        self.daq = devices_dict.get("daq", None)
        self.tiger_controller = None
        self.info = {}
        self.current_channel = None
        self.channels = None
        self.available_channels = None
        self.number_of_frames = None
        self.central_focus = None
        self.is_synthetic = is_synthetic
        self.laser_wavelength = []
        self.ret_pos_dict = {}

        if is_virtual:
            return

        device_ref_dict = {
            "camera": ["type", "serial_number"],
            "filter_wheel": ["type"],
            "zoom": ["type", "servo_id"],
            "shutter": ["type", "channel"],
            "remote_focus_device": ["type", "channel"],
            "galvo": ["type", "channel"],
            "lasers": ["wavelength"],
        }

        # TODO: This cannot be pulled into the repo.
        #  I need help comping up with a more general way to have
        # shared devices.
        # devices_dict['filter_wheel']['ASI'] = devices_dict['stages']['ASI_119060508']

        device_name_dict = {"lasers": "wavelength"}

        laser_list = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["lasers"]
        self.laser_wavelength = [laser["wavelength"] for laser in laser_list]

        # LOAD/START CAMERAS, FILTER_WHEELS, ZOOM, SHUTTERS, REMOTE_FOCUS_DEVICES,
        # GALVOS, AND LASERS
        for device_name in device_ref_dict.keys():
            device_connection = None
            (
                device_config_list,
                device_name_list,
                is_list,
            ) = self.assemble_device_config_lists(
                device_name=device_name, device_name_dict=device_name_dict
            )

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

                # SHARED DEVICES
                elif device_ref_name.startswith("NI") and (
                    device_name == "galvo" or device_name == "remote_focus_device"
                ):
                    device_connection = self.daq

                if device_ref_name.startswith("EquipmentSolutions"):
                    device_connection = self.daq

                if device_ref_name.startswith("ASI") and self.tiger_controller is None:
                    # The first ASI instance of a device connection will be passed to
                    # all other ASI devices as self.tiger_controller
                    device_connection = devices_dict[device_name][device_ref_name]
                    self.tiger_controller = device_connection
                elif (
                    device_ref_name.startswith("ASI")
                    and self.tiger_controller is not None
                ):
                    # If subsequent ASI-based tiger controller devices are included.
                    device_connection = self.tiger_controller

                # LOAD AND START DEVICES
                self.load_and_start_devices(
                    device_name=device_name,
                    is_list=is_list,
                    device_name_list=device_name_list,
                    device_ref_name=device_ref_name,
                    device_connection=device_connection,
                    name=name,
                    i=i,
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
        if type(stage_devices) != ListProxy:
            stage_devices = [stage_devices]

        for i, device_config in enumerate(stage_devices):
            device_ref_name = build_ref_name(
                "_", device_config["type"], device_config["serial_number"]
            )

            if device_ref_name not in devices_dict["stages"]:
                logger.debug("stage has not been loaded!")
                raise Exception("no stage device!")

            # SHARED DEVICES
            if device_ref_name.startswith("GalvoNIStage"):
                devices_dict["stages"][device_ref_name] = self.daq

            if device_ref_name.startswith("ASI") and self.tiger_controller is not None:
                # If the self.tiger_controller is already set, then we can pass it to
                # other devices that are connected to the same controller.
                devices_dict["stages"][device_ref_name] = self.tiger_controller

            stage = start_stage(
                microscope_name=self.microscope_name,
                device_connection=devices_dict["stages"][device_ref_name],
                configuration=self.configuration,
                id=i,
                is_synthetic=is_synthetic,
            )
            for axis in device_config["axes"]:
                self.stages[axis] = stage
                self.info[f"stage_{axis}"] = device_ref_name

            self.stages_list.append((stage, list(device_config["axes"])))

        # connect daq and camera in synthetic mode
        if is_synthetic:
            self.daq.add_camera(self.microscope_name, self.camera)

    def update_data_buffer(self, img_width, img_height, data_buffer, number_of_frames):
        """Update the data buffer for the camera.

        Parameters
        ----------
        img_width : int
            Width of the image.
        img_height : int
            Height of the image.
        data_buffer : numpy.ndarray
            Data buffer for the camera.
        number_of_frames : int
            Number of frames to be acquired.

        Returns
        -------
        None
        """

        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.camera.set_ROI(img_height, img_width)
        self.data_buffer = data_buffer
        self.number_of_frames = number_of_frames

    def move_stage_offset(self, former_microscope=None):
        """Move the stage to the offset position.

        Parameters
        ----------
        former_microscope : str
            Name of the former microscope.

        Returns
        -------
        None
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

        Parameters
        ----------
        None

        Returns
        -------
        None
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
        # Initialize Image Series - Attaches camera buffer and start imaging
        self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)

        # calculate all the waveform
        self.shutter.open_shutter()
        return self.calculate_all_waveform()

    def end_acquisition(self):
        """End the acquisition.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.stop_stage()
        self.daq.stop_acquisition()
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.shutter.close_shutter()
        for k in self.lasers:
            self.lasers[k].turn_off()
        self.current_channel = 0
        self.central_focus = None

    def calculate_all_waveform(self):
        """Calculate all the waveforms.

        Parameters
        ----------
        None

        Returns
        -------
        waveform : dict
            Dictionary of all the waveforms.
        """
        print("calculate waveform adjust")
        # waveform_dict = self.galvo_zero()
        readout_time = self.get_readout_time()
        exposure_times, sweep_times = self.calculate_exposure_sweep_times(readout_time)
        camera_waveform = self.daq.calculate_all_waveforms(
            self.microscope_name, exposure_times, sweep_times
        )
        remote_focus_waveform = self.remote_focus_device.adjust(
            exposure_times, sweep_times
        )
        galvo_waveform = [
            self.galvo[k].adjust(exposure_times, sweep_times) for k in self.galvo
        ]
        # TODO: calculate waveform for galvo stage
        for stage, axes in self.stages_list:
            if type(stage) == GalvoNIStage:
                stage.calculate_waveform(exposure_times, sweep_times)
        # waveform_dict = self.galvo_zero
        waveform_dict = {
            "camera_waveform": camera_waveform,
            "remote_focus_waveform": remote_focus_waveform,
            "galvo_waveform": galvo_waveform,
        }
        return waveform_dict
    
    def galvo_zero(self):
        """Set galvo Amplitude, Offset, and Freq to zero
        """
        print("Galvo Zero Adjust")
        readout_time = self.get_readout_time()
        exposure_times, sweep_times = self.calculate_exposure_sweep_times(readout_time)
        camera_waveform = self.daq.calculate_all_waveforms(
            self.microscope_name, exposure_times, sweep_times
        )
        remote_focus_waveform = self.remote_focus_device.adjust(
            exposure_times, sweep_times
        )
        galvo_waveform = [
            self.galvo[k].adjust_zero(exposure_times, sweep_times) for k in self.galvo
        ]
        # TODO: calculate waveform for galvo stage
        for stage, axes in self.stages_list:
            if type(stage) == GalvoNIStage:
                stage.calculate_waveform(exposure_times, sweep_times)
        waveform_dict = {
            "camera_waveform": camera_waveform,
            "remote_focus_waveform": remote_focus_waveform,
            "galvo_waveform": galvo_waveform,
        }
        return waveform_dict

    def calculate_exposure_sweep_times(self, readout_time):
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

    def prepare_next_channel(self):
        """Prepare the next channel.

        Parameters
        ----------
        None

        Returns
        -------
        None
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
        self.filter_wheel.set_filter(channel["filter"])

        # Camera Settings
        self.current_exposure_time = channel["camera_exposure_time"]
        if (
            self.configuration["experiment"]["CameraParameters"]["sensor_mode"]
            == "Light-Sheet"
        ):
            (
                self.current_exposure_time,
                self.camera_line_interval,
            ) = self.camera.calculate_light_sheet_exposure_time(
                self.current_exposure_time,
                int(
                    self.configuration["experiment"]["CameraParameters"][
                        "number_of_pixels"
                    ]
                ),
            )
            self.camera.set_line_interval(self.camera_line_interval)
        self.camera.set_exposure_time(self.current_exposure_time)

        # Laser Settings
        current_laser_index = channel["laser_index"]
        for k in self.lasers:
            self.lasers[k].turn_off()
        self.lasers[str(self.laser_wavelength[current_laser_index])].set_power(
            channel["laser_power"]
        )
        self.lasers[str(self.laser_wavelength[current_laser_index])].turn_on()

        # stop daq before writing new waveform
        self.daq.stop_acquisition()
        # prepare daq: write waveform
        self.daq.prepare_acquisition(channel_key, self.current_exposure_time)

        # Add Defocus term
        # Assume wherever we start is the central focus
        # TODO: is this the correct assumption?
        if self.central_focus is None:
            try:
                self.central_focus = self.get_stage_position()["f_pos"]
            except KeyError:
                self.central_focus = 0.0
        self.move_stage(
            {"f_abs": self.central_focus + float(channel["defocus"])},
            wait_until_done=True,
            update_focus=False,
        )

    def get_readout_time(self):
        """Get readout time from camera.

        Get the camera readout time if we are in normal mode.
        Return a -1 to indicate when we are not in normal mode.
        This is needed in daq.calculate_all_waveforms()

        Parameters
        ----------
        None

        Returns
        -------
        readout_time : float
            Camera readout time in seconds or -1 if not in Normal mode.
        """
        readout_time = 0
        if (
            self.configuration["experiment"]["CameraParameters"]["sensor_mode"]
            == "Normal"
        ):
            readout_time, _ = self.camera.calculate_readout_time()
        return readout_time

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
        None
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
        """Stop stage.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.ask_stage_for_position = True

        for stage, axes in self.stages_list:
            stage.stop()

    def get_stage_position(self):
        """Get stage position.

        Parameters
        ----------
        None

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
        readout_time = self.get_readout_time()
        exposure_times, sweep_times = self.calculate_exposure_sweep_times(readout_time)
        self.remote_focus_device.move(exposure_times, sweep_times, offset)

    def update_stage_limits(self, limits_flag=True):
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

        devices = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ][device_name]

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

        Returns
        -------
        None
        """
        # Import start_device classes
        try:
            exec(
                f"start_{device_name}=importlib.import_module("
                f"'aslm.model.device_startup_functions').start_{device_name}"
            )
        except AttributeError:
            print(f"Could not import start_{device_name}")
            print(f"Could not load device {device_name}")

        # Start the devices
        if is_list:
            exec(
                f"self.{device_name}['{device_name_list[i]}'] = "
                f"start_{device_name}(name, device_connection, self.configuration, "
                f"i, self.is_synthetic)"
            )
            if device_name in device_name_list[i]:
                self.info[device_name_list[i]] = device_ref_name
        else:
            exec(
                f"self.{device_name} = start_{device_name}(name, "
                f"device_connection, self.configuration, self.is_synthetic)"
            )
            self.info[device_name] = device_ref_name

    def terminate(self):
        """Close hardware explicitly."""
        # self.camera.close_camera()
        # print("Camera Closed")
        self.galvo_zero()
        # try:
        #     #turn off galvo on exit
        #     for k in self.galvo:
        #         self.galvo_zero()
        #         #self.galvo[k].close_task()
        #         print(self.galvo[k]) 
        #         print("closed")
        # except AttributeError:
        #     #print("Galvo Passed")
        #     pass
        # set galvo waveform to zero
        try:
            # Currently only for RemoteFocusEquipmentSolutions
            self.remote_focus_device.close_connection()
        except AttributeError:
            pass
        self.camera.close_camera()
        print("Camera Closed")

       
