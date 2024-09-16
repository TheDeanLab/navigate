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
#

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from navigate.model.devices.camera.base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class HamamatsuBase(CameraBase):
    """HamamatsuOrca camera class.

    This is the default parent class for Hamamatsu Cameras.
    This includes the ORCA Flash 4.0, Fusion, Lightning, and Fire.
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

        #: str: Name of the microscope
        self.microscope_name = microscope_name

        #: object: Device connection
        self.device_connection = device_connection

        #: dict: Configuration settings
        self.configuration = configuration

        #: dict: Camera parameters
        self.camera_parameters["x_pixels"] = self.camera_controller.max_image_width
        self.camera_parameters["y_pixels"] = self.camera_controller.max_image_height
        self.camera_parameters["x_pixels_min"] = self.camera_controller.min_image_width
        self.camera_parameters["y_pixels_min"] = self.camera_controller.min_image_height
        self.camera_parameters[
            "x_pixels_step"
        ] = self.camera_controller.step_image_width
        self.camera_parameters[
            "y_pixels_step"
        ] = self.camera_controller.step_image_height
        self.minimum_exposure_time, _, _ = self.camera_controller.get_property_range(
            "exposure_time"
        )

        #: object: Camera controller
        if self.camera_controller.get_property_value("readout_speed"):
            _, speed_max, _ = self.camera_controller.get_property_range("readout_speed")
            if speed_max is not None:
                self.camera_controller.set_property_value(
                    "readout_speed", int(speed_max)
                )
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

    def __repr__(self):
        """Return representation of HamamatsuBase class.

        Returns
        -------
        str
            Representation of HamamatsuBase class.
        """
        return (
            f"HamamatsuBase("
            f"{self.microscope_name}, "
            f"{self.device_connection}, "
            f"{self.configuration})"
        )

    def __str__(self):
        """Return string representation of HamamatsuOrca class.

        Returns
        -------
        str
            String representation of HamamatsuOrca class.
        """
        return "HamamatsuBase"

    def __del__(self):
        """Delete HamamatsuOrca class."""
        pass

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
            "subarray_vsize",
            "subarray_hsize",
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
            "readout_time",
        ]
        for param in params:
            print(param, self.camera_controller.get_property_value(param))
            logger.info(f"{param}, {self.camera_controller.get_property_value(param)}")

        print(
            "*** exposure time range:",
            self.camera_controller.get_property_range("exposure_time"),
        )

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
            self.camera_parameters[
                "x_pixels_min"
            ] = self.camera_controller.min_image_width
            self.camera_parameters[
                "y_pixels_min"
            ] = self.camera_controller.min_image_height
            self.camera_parameters[
                "x_pixels_step"
            ] = self.camera_controller.step_image_width
            self.camera_parameters[
                "y_pixels_step"
            ] = self.camera_controller.step_image_height
        else:
            print("Camera mode not supported")
            logger.debug("Camera mode not supported")

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
            self.camera_controller.set_property_value(
                "readout_direction", readout_direction_dict[mode]
            )
        else:
            print("Camera readout direction not supported")
            logger.debug("Camera readout direction not supported")

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

        """
        readout_time = self.camera_controller.get_property_value("readout_time")

        # with camera internal delay
        return readout_time  # + 4 * self.minimum_exposure_time

    def set_exposure_time(self, exposure_time):
        """Set HamamatsuOrca exposure time.

        Note
        ----
            Units of the Hamamatsu API are in seconds.

        Parameters
        ----------
        exposure_time : float
            Exposure time in seconds.
        """
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

    def set_ROI(self, roi_width=2048, roi_height=2048, center_x=1024, center_y=1024):
        """Change the size of the active region on the camera.

        Parameters
        ----------
        roi_width : int
            Width of active camera region.
        roi_height : int
            Height of active camera region.
        center_x : int
            X position of the center of view
        center_y : int
            Y position of the center of view

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        # Get the Maximum Number of Pixels from the Configuration File
        camera_height = self.camera_parameters["y_pixels"]
        camera_width = self.camera_parameters["x_pixels"]

        roi_top = center_y - roi_height // 2
        roi_bottom = center_y + roi_height // 2
        roi_left = center_x - roi_width // 2
        roi_right = center_x + roi_width // 2

        step_image_height = self.camera_controller.step_image_height
        step_image_width = self.camera_controller.step_image_width

        if (
            roi_top < 0
            or roi_bottom > camera_height
            or roi_left < 0
            or roi_right > camera_width
            or roi_top % step_image_height != 0
            or roi_bottom % step_image_height != 0
            or roi_left % step_image_width != 0
            or roi_right % step_image_width != 0
        ):
            logger.debug(f"can't set roi to {roi_width} and {roi_height}")
            return False

        # Set ROI
        self.x_pixels, self.y_pixels = self.camera_controller.set_ROI(
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

        return self.x_pixels == roi_width and self.y_pixels == roi_height

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        """Initialize HamamatsuOrca image series.

        Parameters
        ----------
        data_buffer :
            List of SharedNDArrays of shape=(self.img_height,
            self.img_width) and dtype="uint16"
            Default is None.
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
            Frame ids from HamamatsuOrca camera.
        """
        return self.camera_controller.get_frames()


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

        # self.minimum_exposure_time = 6.304 * 10 ** -6

        logger.info(self.__repr__())

    def __repr__(self):
        return (
            f"HamamatsuOrcaLightning("
            f"{self.microscope_name}, "
            f"{self.device_connection}, "
            f"{self.configuration})"
        )

    def __str__(self):
        """Return string representation of HamamatsuOrcaLightning class.

        Returns
        -------
        str
            String representation of HamamatsuOrcaLightning class.
        """
        return "HamamatsuOrcaLightning"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time, shutter_width
    ):
        """Calculate light sheet exposure time.

        Parameters
        ----------
        full_chip_exposure_time : float
            Full chip exposure time in seconds.
        shutter_width : int
            Shutter width.

        Returns
        -------
        exposure_time : float
            Exposure time in seconds.
        camera_line_interval : float
            Camera line interval in seconds.
        full_chip_exposure_time : float
            Full chip exposure time in seconds.
        """

        camera_line_interval = full_chip_exposure_time / (
            6 + (shutter_width + self.y_pixels) / 4
        )
        self.camera_parameters["line_interval"] = camera_line_interval

        maximum_internal_line_interval = 0.0002  # 200.0 us
        if camera_line_interval > maximum_internal_line_interval:
            camera_line_interval = maximum_internal_line_interval
            full_chip_exposure_time = camera_line_interval * (
                6 + (shutter_width + self.y_pixels) / 4
            )

        exposure_time = camera_line_interval * ((shutter_width + 3) // 4)
        return exposure_time, camera_line_interval, full_chip_exposure_time


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
            "Top-to-Bottom",
            "Bottom-to-Top",
            "Bidirectional",
            "Rev. Bidirectional",
        ]

        # self.minimum_exposure_time = 7.309 * 10 ** -6  # 7.309 us

        self.camera_parameters["x_pixels"] = self.camera_controller.get_property_value(
            "image_width"
        )

        self.camera_parameters["y_pixels"] = self.camera_controller.get_property_value(
            "image_height"
        )

        logger.info(self.__repr__())

    def __repr__(self):
        return (
            f"HamamatsuOrcaFire("
            f"{self.microscope_name}, "
            f"{self.device_connection}, "
            f"{self.configuration})"
        )

    def __str__(self):
        """Return string representation of HamamatsuOrcaFire class.

        Returns
        -------
        str
            String representation of HamamatsuOrcaFire class.
        """
        return "HamamatsuOrcaFire"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time, shutter_width
    ):
        """Convert normal mode exposure time to light-sheet mode exposure time.
        Calculate the parameters for an acquisition

        Parameters
        ----------
        full_chip_exposure_time : float
            Normal mode exposure time in seconds.
        shutter_width : int
            Width of light-sheet rolling shutter.

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time (s).
        camera_line_interval : float
            HamamatsuOrca line interval duration (s).
        full_chip_exposure_time : float
            Updated full chip exposure time (s).
        """
        # 4H delay, (Vn/2+5)H readout
        camera_line_interval = full_chip_exposure_time / (
            9 + (shutter_width + self.y_pixels) / 2
        )

        maximum_internal_line_interval = 0.0002339  # 233.9 us
        if camera_line_interval > maximum_internal_line_interval:
            camera_line_interval = maximum_internal_line_interval
            full_chip_exposure_time = camera_line_interval * (
                9 + (shutter_width + self.y_pixels) / 2
            )

        self.camera_parameters["line_interval"] = camera_line_interval

        # round up exposure time
        exposure_time = camera_line_interval * ((shutter_width + 1) // 2)
        return exposure_time, camera_line_interval, full_chip_exposure_time


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
            "Top-to-Bottom",
            "Bottom-to-Top",
        ]

        # self.minimum_exposure_time = 9.74436 * 10 ** -6

        logger.info(self.__repr__())

    def __repr__(self):
        """Return representation of HamamatsuOrca class.

        Returns
        -------
        str
            Representation of HamamatsuOrca class.
        """
        return (
            f"HamamatsuOrca("
            f"{self.microscope_name}, "
            f"{self.device_connection}, "
            f"{self.configuration})"
        )

    def __str__(self):
        """Return string representation of HamamatsuOrca class.

        Returns
        -------
        str
            String representation of HamamatsuOrca class.
        """
        return "HamamatsuOrca"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time, shutter_width
    ):
        """Convert normal mode exposure time to light-sheet mode exposure time.
        Calculate the parameters for an acquisition

        Parameters
        ----------
        full_chip_exposure_time : float
            Normal mode exposure time in seconds.
        shutter_width : int
            Width of light-sheet rolling shutter.

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time (s).
        camera_line_interval : float
            HamamatsuOrca line interval duration (s).
        full_chip_exposure_time : float
            Updated full chip exposure time (s).
        """
        camera_line_interval = full_chip_exposure_time / (
            10 + shutter_width + self.y_pixels
        )

        maximum_internal_line_interval = 0.1  # 100ms
        if camera_line_interval > maximum_internal_line_interval:
            camera_line_interval = maximum_internal_line_interval
            full_chip_exposure_time = camera_line_interval * (
                10 + shutter_width + self.y_pixels
            )

        self.camera_parameters["line_interval"] = camera_line_interval * shutter_width

        # round up exposure time
        exposure_time = camera_line_interval * shutter_width
        return exposure_time, camera_line_interval, full_chip_exposure_time


class HamamatsuOrcaFusion(HamamatsuBase):
    """HamamatsuOrcaFusion camera class."""

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize HamamatsuOrcaFusion class.

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
            "Top-to-Bottom",
            "Bottom-to-Top",
        ]

        logger.info(self.__repr__())

    def __repr__(self):
        return (
            f"HamamatsuOrcaFusion("
            f"{self.microscope_name}, "
            f"{self.device_connection}, "
            f"{self.configuration})"
        )

    def __str__(self):
        """Return string representation of HamamatsuOrcaFusion class.

        Returns
        -------
        str
            String representation of HamamatsuOrcaFusion class.
        """
        return "HamamatsuOrcaFusion"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time, shutter_width
    ):
        """Calculate light sheet exposure time.

        Parameters
        ----------
        full_chip_exposure_time : float
            Full chip exposure time in seconds.
        shutter_width : int
            Shutter width.

        Returns
        -------
        exposure_time : float
            Exposure time in seconds.
        camera_line_interval : float
            Camera line interval in seconds.
        full_chip_exposure_time : float
            Full chip exposure time in seconds.
        """

        camera_line_interval = full_chip_exposure_time / (
            4 + shutter_width + self.y_pixels
        )

        maximum_internal_line_interval = 963.8e-6  # 963.8 us
        if camera_line_interval > maximum_internal_line_interval:
            camera_line_interval = maximum_internal_line_interval
            full_chip_exposure_time = camera_line_interval * (
                4 + shutter_width + self.y_pixels
            )

        self.camera_parameters["line_interval"] = camera_line_interval * shutter_width

        # round up exposure time
        exposure_time = camera_line_interval * shutter_width
        return exposure_time, camera_line_interval, full_chip_exposure_time
