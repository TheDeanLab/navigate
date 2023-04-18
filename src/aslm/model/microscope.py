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

    Examples
    --------
    >>> microscope = Microscope(configuration,
    >>> data_buffer, daq, microscope_name, number_of_frames)
    >>> microscope.update_data_buffer(img_width, img_height,
    >>> data_buffer, number_of_frames)
    >>> microscope.move_stage_offset(former_microscope=None)
    >>> microscope.end_acquisition()
    >>> microscope.get_readout_time()

    """

    def __init__(
        self, name, configuration, devices_dict, is_synthetic=False, is_virtual=False
    ):

        # Initialize microscope object
        self.microscope_name = name
        self.configuration = configuration
        self.data_buffer = None
        self.stages = {}
        self.cameras = {}
        self.lasers = {}
        self.galvo = {}
        self.daq = devices_dict.get("daq", None)
        self.info = {}

        self.current_channel = None
        self.channels = None
        self.available_channels = None
        self.number_of_frames = None
        self.central_focus = None

        self.laser_wavelength = []

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
            "mirror": ["type"]
        }
        device_name_dict = {"lasers": "wavelength"}

        laser_list = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["lasers"]
        self.laser_wavelength = [laser["wavelength"] for laser in laser_list]

        # load/start all the devices listed in device_ref_dict
        for device_name in device_ref_dict.keys():
            device_connection = None
            device_config_list = []
            device_name_list = []

            if (
                type(configuration["configuration"]["microscopes"][name][device_name])
                == ListProxy
            ):
                i = 0
                for d in configuration["configuration"]["microscopes"][name][
                    device_name
                ]:
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
                device_config_list.append(
                    configuration["configuration"]["microscopes"][name][device_name]
                )
                is_list = False

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
                elif device_ref_name.startswith("NI") and (
                    device_name == "galvo" or device_name == "remote_focus_device"
                ):
                    # TODO: Remove this. We should not have this hardcoded.
                    device_connection = self.daq

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
                        f"start_{device_name}(name, device_connection, configuration, "
                        f"i, is_synthetic)"
                    )
                    if device_name in device_name_list[i]:
                        self.info[device_name_list[i]] = device_ref_name
                else:
                    exec(
                        f"self.{device_name} = start_{device_name}(name, "
                        f"device_connection, configuration, is_synthetic)"
                    )
                    self.info[device_name] = device_ref_name

                if device_connection is None and device_ref_name is not None:
                    if device_name not in devices_dict:
                        devices_dict[device_name] = {}
                    devices_dict[device_name][device_ref_name] = (
                        getattr(self, device_name)[device_name_list[i]]
                        if is_list
                        else getattr(self, device_name)
                    )

        # cameras (handle camera list similar to stages...)
        # camera_devices = self.configuration['configuration']['microscopes'][self.microscope_name]['camera']['hardware']
        # if type(camera_devices) != ListProxy:
        #     camera_devices = [camera_devices]
        # for i, device_config in enumerate(camera_devices):
        #     device_ref_name = build_ref_name('_', device_config['type'], device_config['serial_number'])            
        #     if device_ref_name not in devices_dict['camera']:
        #         logger.debug(f'Camera {device_ref_name} has not been loaded!')
        #         raise Exception('No camera device!')
        #     print(f"{device_ref_name} : {devices_dict['camera'][device_ref_name]}")
        #     self.cameras[device_ref_name] = start_camera(self.microscope_name, devices_dict['camera'][device_ref_name], self.configuration, i, is_synthetic)

        # self.camera = list(self.cameras.values())[0] # just use the first one for now...

        # print('>>> Use Camera:')
        # print(self.camera.camera_controller._serial_number)

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
            if device_ref_name.startswith("GalvoNIStage"):
                # TODO: Remove this. We should not have this hardcoded.
                devices_dict["stages"][device_ref_name] = self.daq

            stage = start_stage(
                self.microscope_name,
                devices_dict["stages"][device_ref_name],
                self.configuration,
                i,
                is_synthetic,
            )
            for axis in device_config["axes"]:
                self.stages[axis] = stage
                self.info[f"stage_{axis}"] = device_ref_name

        # flatten the mirror
        self.mirror.flat()

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

        Examples
        --------
        >>> microscope.update_data_buffer(img_width=512,
        >>> img_height=512, data_buffer=None, number_of_frames=1)

        """

        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.camera.set_ROI(img_width, img_height)
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

        Examples
        --------
        >>> microscope.move_stage_offset(former_microscope="microscope1")

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
        pos_dict = self.get_stage_position()
        for axes in self.stages:
            pos = (
                pos_dict[axes + "_pos"]
                + self_offset_dict[axes + "_offset"]
                - former_offset_dict[axes + "_offset"]
            )
            self.stages[axes].move_absolute({axes + "_abs": pos}, wait_until_done=True)

    def prepare_acquisition(self):
        """Prepare the acquisition.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> microscope.prepare_acquisition()

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

        Examples
        --------
        >>> microscope.end_acquisition()
        """
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

        Examples
        --------
        >>> waveform = microscope.calculate_all_waveform()

        """
        readout_time = self.get_readout_time()
        camera_waveform = self.daq.calculate_all_waveforms(
            self.microscope_name, readout_time
        )
        remote_focus_waveform = self.remote_focus_device.adjust(readout_time)
        galvo_waveform = [self.galvo[k].adjust(readout_time) for k in self.galvo]
        #TODO: calculate waveform for galvo stage
        for axis in self.stages:           
            if type(self.stages[axis]) == GalvoNIStage:
                self.stages[axis].calculate_waveform()
        waveform_dict = {
            "camera_waveform": camera_waveform,
            "remote_focus_waveform": remote_focus_waveform,
            "galvo_waveform": galvo_waveform,
        }
        return waveform_dict

    def prepare_next_channel(self):
        """Prepare the next channel.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> microscope.prepare_next_channel()
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
        self.lasers[str(self.laser_wavelength[current_laser_index])].set_power(
            channel["laser_power"]
        )
        for k in self.lasers:
            self.lasers[k].turn_off()
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

        Examples
        --------
        >>> readout_time = microscope.get_readout_time()

        """
        readout_time = 0
        if (
            self.configuration["experiment"]["CameraParameters"]["sensor_mode"]
            == "Normal"
        ):
            readout_time, _ = self.camera.calculate_readout_time()
        return readout_time

    def move_stage(self, pos_dict, wait_until_done=False):
        """Move stage to a position.

        Parameters
        ----------
        pos_dict : dict
            Dictionary of stage positions.
        wait_until_done : bool, optional
            Wait until stage is done moving, by default False

        Returns
        -------
        None

        Examples
        --------
        >>> microscope.move_stage({"x_abs": 0, "y_abs": 0, "z_abs": 0, "f_abs": 0})
        """

        success = True
        for pos_axis in pos_dict:
            axis = pos_axis[: pos_axis.index("_")]
            success = (
                self.stages[axis].move_absolute(
                    {pos_axis: pos_dict[pos_axis]}, wait_until_done
                )
                and success
            )
        return success

    def stop_stage(self):
        """Stop stage.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> microscope.stop_stage()
        """

        for axis in self.stages:
            self.stages[axis].stop()

    def get_stage_position(self):
        """Get stage position.

        Parameters
        ----------
        None

        Returns
        -------
        stage_position : dict
            Dictionary of stage positions.

        Examples
        --------
        >>> stage_position = microscope.get_stage_position()
        """

        ret_pos_dict = {}
        for axis in self.stages:
            pos_axis = axis + "_pos"
            temp_pos = self.stages[axis].report_position()
            ret_pos_dict[pos_axis] = temp_pos[pos_axis]
        return ret_pos_dict
