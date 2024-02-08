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

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from navigate.model.devices.camera.camera_base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class HamamatsuBase(CameraBase):
    """HamamatsuOrca camera class.

    This is the default parent class for Hamamatsu Cameras.
    This includes the ORCA Flash 4.0, Fusion, Lightning, and Fire.

    **Configuration**::

        hardware:
          camera:
            -
                type: HamamatsuOrca
                serial_number: 302158
            -
                type: HamamatsuOrca
                serial_number: 302159
        ...

        microscopes:
          microscope_name:
            camera:
              hardware:
                name: camera
                type: HamamatsuOrca
                serial_number: 302352
              lightsheet_rolling_shutter_width: 608
              defect_correct_mode: 2.0 # Off: 1.0, On: 2.0
              delay_percent: 10
              pulse_percent: 1
              x_pixels_step: 4
              y_pixels_step: 4
              x_pixels_min: 4
              y_pixels_min: 4
              exposure_time_range:
                min: 1
                max: 1000
                step: 1
              flip_x: False
              flip_y: False
    """

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize HamamatsuOrca class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
            Global configuration of the microscope
        """
        super().__init__(microscope_name, device_connection, configuration)

        #: dict: Camera parameters
        self.camera_parameters["x_pixels"] = self.camera_controller.max_image_width
        self.camera_parameters["y_pixels"] = self.camera_controller.max_image_height
        self.camera_parameters["x_pixels_min"] = self.camera_controller.min_image_width
        self.camera_parameters["y_pixels_min"] = self.camera_controller.min_image_height
        self.camera_parameters["x_pixels_step"] = self.camera_controller.step_image_width
        self.camera_parameters["y_pixels_step"] = self.camera_controller.step_image_height
        self.minimum_exposure_time = 0.001

        #: object: Camera controller
        if self.camera_controller.get_property_value("readout_speed"):
            _, speed_max, _ = self.camera_controller.get_property_range("readout_speed")
            if speed_max is not None:
                self.camera_controller.set_property_value("readout_speed", int(speed_max))
                self.camera_parameters["readout_speed"] = int(speed_max)
            else:
                self.camera_controller.set_property_value("readout_speed", 1)
                self.camera_parameters["readout_speed"] = 1

        self.camera_parameters[
            "pixel_size_in_microns"
        ] = self.camera_controller.get_property_value("pixel_width")

        # Values are pulled from the CameraParameters section of the configuration.yml
        # file. Exposure time converted here from milliseconds to seconds.

        self.camera_controller.set_property_value(
            "defect_correct_mode", self.camera_parameters["defect_correct_mode"]
        )
        self.camera_controller.set_property_value(
            "trigger_active", self.camera_parameters["trigger_active"]
        )
        self.camera_controller.set_property_value(
            "trigger_mode", self.camera_parameters["trigger_mode"]
        )
        self.camera_controller.set_property_value(
            "trigger_polarity", self.camera_parameters["trigger_polarity"]
        )
        self.camera_controller.set_property_value(
            "trigger_source", self.camera_parameters["trigger_source"]
        )

        logger.info("HamamatsuOrca Initialized")

    def __del__(self):
        """Delete HamamatsuOrca class."""
        logger.info("HamamatsuOrca Shutdown")

    @property
    def serial_number(self):
        """Get Camera Serial Number

        Returns
        -------
        serial_number : str
            Serial number for the camera.
        """
        return self.camera_controller._serial_number

    def report_settings(self):
        """Print Camera Settings.

        Prints the current camera settings to the console and the log file."""
        params = [
            "defect_correct_mode",
            "sensor_mode",
            "binning",
            "subarray_mode",
            "readout_speed",
            "trigger_active",
            "trigger_mode",
            "trigger_polarity",
            "trigger_source",
            "internal_line_interval",
            "internal_line_speed",
            "image_height",
            "image_width",
            "exposure_time",
        ]
        for param in params:
            print(param, self.camera_controller.get_property_value(param))
            logger.info(f"{param}, {self.camera_controller.get_property_value(param)}")

    def close_camera(self):
        """Close HamamatsuOrca Camera"""
        self.camera_controller.dev_close()

    def set_sensor_mode(self, mode):
        """Set HamamatsuOrca sensor mode.

        Parameters
        ----------
        mode : str
            'Normal' or 'Light-Sheet'
        """
        modes_dict = {"Normal": 1, "Light-Sheet": 12}
        if mode in modes_dict:
            self.camera_controller.set_property_value("sensor_mode", modes_dict[mode])

            # Update minimum image sizes based on scan mode
            (
                self.camera_controller.min_image_width,
                _,
                self.camera_controller.step_image_width,
            ) = self.camera_controller.get_property_range("subarray_hsize")
            (
                self.camera_controller.min_image_height,
                _,
                self.camera_controller.step_image_height,
            ) = self.camera_controller.get_property_range("subarray_vsize")
            # update configuration dict
            self.camera_parameters["x_pixels_min"] = self.camera_controller.min_image_width
            self.camera_parameters["y_pixels_min"] = self.camera_controller.min_image_height
            self.camera_parameters["x_pixels_step"] = self.camera_controller.step_image_width
            self.camera_parameters["y_pixels_step"] = self.camera_controller.step_image_height
        else:
            print("Camera mode not supported")
            logger.info("Camera mode not supported")

    def set_readout_direction(self, mode):
        """Set HamamatsuOrca readout direction.

        Parameters
        ----------
            mode : str
                'Top-to-Bottom', 'Bottom-to-Top', 'bytrigger', or 'diverge'.
        """
        readout_direction_dict = {
            "Top-to-Bottom": 1.0,
            "Bottom-to-Top": 2.0,
            "bytrigger": 3.0,
            "diverge": 5.0,
            "Bidirectional": 6.0,
            "Rev. Bidirectional": 7.0,
        }

        if mode in readout_direction_dict:
            self.camera_controller.set_property_value("readout_direction", readout_direction_dict[mode])
        else:
            print("Camera readout direction not supported")
            logger.info("Camera readout direction not supported")

    def calculate_readout_time(self):
        """Calculate duration of time needed to readout an image.

        Calculates the readout time and maximum frame rate according to the camera
        configuration settings.
        Assumes model C13440 with Camera Link communication from Hamamatsu.
        Currently pulling values directly from the camera.

        Returns
        -------
        readout_time : float
            Duration of time needed to readout an image.
        max_frame_rate : float
            Maximum framerate for a given camera acquisition mode.

        TODO: I think self.camera_controller.get_property_value("readout_time") pulls
              out the actual readout_time
              calculated here (i.e. we don't need to do the calculations).
        """
        h = self.camera_controller.get_property_value("readout_time")
        vn = self.camera_controller.get_property_value("subarray_vsize")
        sensor_mode = self.camera_controller.get_property_value("sensor_mode")
        exposure_time = self.camera_controller.get_property_value("exposure_time")
        trigger_source = self.camera_controller.get_property_value("trigger_source")
        trigger_active = self.camera_controller.get_property_value("trigger_active")

        if sensor_mode == 1:
            #  Area sensor mode operation
            if trigger_source == 1:
                # Internal Trigger Source
                max_frame_rate = 1 / ((vn / 2) * h)
                readout_time = exposure_time - ((vn / 2) * h)

            if trigger_active == 1 or 2:
                #  External Trigger Source
                #  Edge == 1, Level == 2
                max_frame_rate = 1 / ((vn / 2) * h + exposure_time + 10 * h)
                readout_time = exposure_time - ((vn / 2) * h + exposure_time + 10 * h)

            if trigger_active == 3:
                #  External Trigger Source
                #  Synchronous Readout == 3
                max_frame_rate = 1 / ((vn / 2) * h + 5 * h)
                readout_time = exposure_time - ((vn / 2) * h + 5 * h)

            readout_time = h
            max_frame_rate = 1.0 / (exposure_time + readout_time)

        elif sensor_mode == 12:
            #  Progressive sensor mode operation
            max_frame_rate = 1 / (exposure_time + (vn + 10) * h)
            readout_time = exposure_time - 1 / (exposure_time + (vn + 10) * h)

        else:
            print(f"Hamamatsu Camera. Sensor mode {sensor_mode} not supported")
            logger.error(f"Hamamatsu Camera. Sensor mode {sensor_mode} not supported")
            max_frame_rate = 0
            readout_time = 0
        return readout_time, max_frame_rate

    def set_exposure_time(self, exposure_time):
        """Set HamamatsuOrca exposure time.

        Note
        ----
            Units of the Hamamatsu API are in seconds.
            Units for the software are in milliseconds. Conversion is done here.

        Parameters
        ----------
        exposure_time : float
            Exposure time in milliseconds.
        """
        exposure_time = ((exposure_time / 1000) // self.minimum_exposure_time) * self.minimum_exposure_time
        return self.camera_controller.set_property_value("exposure_time", exposure_time)

    def set_line_interval(self, line_interval_time):
        """Set HamamatsuOrca line interval.

        Parameters
        ----------
        line_interval_time : float
            Line interval duration.
        """
        return self.camera_controller.set_property_value(
            "internal_line_interval", line_interval_time
        )

    def get_line_interval(self):
        """Get HamamatsuOrca line interval.

        Returns
        -------
        line_interval_time : float
            Line interval duration.
        """
        self.line_interval = self.camera_controller.get_property_value(
            "internal_line_interval"
        )

    def set_binning(self, binning_string):
        """Set HamamatsuOrca binning mode.

        Parameters
        ----------
        binning_string : str
            Desired binning properties (e.g., '1x1', '2x2', '4x4', '8x8', '16x16',
            '1x2', '2x4')

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        binning_dict = {
            "1x1": 1,
            "2x2": 2,
            "4x4": 4,
            # '8x8': 8,
            # '16x16': 16,
            # '1x2': 102,
            # '2x4': 204
        }
        if binning_string not in binning_dict.keys():
            logger.debug(f"can't set binning to {binning_string}")
            print(f"can't set binning to {binning_string}")
            return False
        self.camera_controller.set_property_value(
            "binning", binning_dict[binning_string]
        )
        return True

    def set_ROI(self, roi_height=2048, roi_width=2048):
        """Change the size of the active region on the camera.

        Parameters
        ----------
        roi_height : int
            Height of active camera region.
        roi_width : int
            Width of active camera region.

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        # Get the Maximum Number of Pixels from the Configuration File
        camera_height = self.camera_parameters["y_pixels"]
        camera_width = self.camera_parameters["x_pixels"]

        if (
            roi_height > camera_height
            or roi_width > camera_width
            or roi_height < 1
            or roi_width < 1
        ):
            logger.debug(f"can't set roi to {roi_width} and {roi_height}")
            return False

        # Calculate Location of Image Edges
        roi_top = (camera_height - roi_height) / 2
        roi_bottom = roi_top + roi_height
        roi_left = (camera_width - roi_width) / 2
        roi_right = roi_left + roi_width

        # Set ROI
        x_pixels, y_pixels = self.camera_controller.set_ROI(
            roi_left, roi_top, roi_right, roi_bottom
        )

        logger.info(
            "HamamatsuOrca - subarray_hpos, "
            f"{self.camera_controller.get_property_value('subarray_hpos')}"
        )
        logger.info(
            "HamamatsuOrca - subarray_hsize, "
            f"{self.camera_controller.get_property_value('subarray_hsize')}"
        )
        logger.info(
            "HamamatsuOrca - subarray_vpos, "
            f"{self.camera_controller.get_property_value('subarray_vpos')}"
        )
        logger.info(
            "HamamatsuOrca - subarray_vsize, "
            f"{self.camera_controller.get_property_value('subarray_vsize')}"
        )

        return x_pixels == roi_width and y_pixels == roi_height

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        """Initialize HamamatsuOrca image series.

        Parameters
        ----------
        data_buffer : int
            Size of the data to buffer.  Default is None.
        number_of_frames : int
            Number of frames.  Default is 100.
        """
        self.camera_controller.start_acquisition(data_buffer, number_of_frames)
        self.is_acquiring = True

    def close_image_series(self):
        """Close image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        self.camera_controller.stop_acquisition()
        self.is_acquiring = False

    def get_new_frame(self):
        """Get frame from HamamatsuOrca camera.

        Returns
        -------
        frame : numpy.ndarray
            Frame from HamamatsuOrca camera.
        """
        return self.camera_controller.get_frames()

    def get_minimum_waiting_time(self):
        """Get minimum waiting time for HamamatsuOrca.

        This function gets the timing information from the camera device
        cyclic_trigger_period, minimum_trigger_blank, minimum_trigger_interval
        'cyclic_trigger_period' if current device is 0.

        According to the documentation, trigger_blank should be bigger than
        trigger_interval.

        Returns
        -------
        trigger_blank : float
            Minimum waiting time.
        """
        # cyclic_trigger =
        #   self.camera_controller.get_property_value('cyclic_trigger_period')
        trigger_blank = self.camera_controller.get_property_value(
            "minimum_trigger_blank"
        )
        # trigger_interval =
        #   self.camera_controller.get_property_value('minimum_trigger_interval')
        return trigger_blank


class HamamatsuOrcaLightning(HamamatsuBase):
    """HamamatsuOrcaLightning camera class."""

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize HamamatsuOrcaLightning class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
            Global configuration of the microscope
        """
        HamamatsuBase.__init__(self, microscope_name, device_connection, configuration)

        self.camera_parameters["supported_readout_directions"] = ["Top-to-Bottom"]

        self.minimum_exposure_time = 6.304 * 10 ** -6

        logger.info("HamamatsuOrcaLightning Initialized")

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time, shutter_width
    ):
        """Calculate light sheet exposure time.

        Parameters
        ----------
        full_chip_exposure_time : float
            Full chip exposure time.
        shutter_width : int
            Shutter width.

        Returns
        -------
        exposure_time : float
            Exposure time.
        camera_line_interval : float
            Camera line interval.
        """

        camera_line_interval = (full_chip_exposure_time / 1000) / (
            (shutter_width + self.y_pixels - 1) / 4
        )
        self.camera_parameters["line_interval"] = camera_line_interval
        exposure_time = camera_line_interval * (shutter_width / 4) * 1000
        return exposure_time, camera_line_interval


class HamamatsuOrcaFire(HamamatsuBase):
    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize HamamatsuOrcaFire class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
            Global configuration of the microscope
        """
        HamamatsuBase.__init__(self, microscope_name, device_connection, configuration)
        self.camera_parameters["supported_readout_directions"] = [
            "Top-to-Bottom", "Bottom-to-Top", "Bidirectional", "Rev. Bidirectional"]

        self.minimum_exposure_time = 7.309 * 10 ** -6  # 7.309 us

        self.camera_parameters["x_pixels"] = self.camera_controller.get_property_value(
            "image_width")

        self.camera_parameters["y_pixels"] = self.camera_controller.get_property_value(
            "image_height")

        logger.info("HamamatsuOrcaFire Initialized")


class HamamatsuOrca(HamamatsuBase):
    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize HamamatsuOrca class.

        This is for controlling the Orca Flash 4.0.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
            Global configuration of the microscope
        """
        HamamatsuBase.__init__(self, microscope_name, device_connection, configuration)

        self.camera_parameters["supported_readout_directions"] = [
            "Top-to-Bottom", "Bottom-to-Top"]

        self.minimum_exposure_time = 9.74436 * 10 ** -6

        logger.info("HamamatsuOrca Initialized")