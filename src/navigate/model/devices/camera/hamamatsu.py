# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
from typing import Any, Optional

# Third Party Imports

# Local Imports
from navigate.model.devices.camera.base import CameraBase
from navigate.model.devices.device_types import SequenceDevice
from navigate.model.devices.APIs.hamamatsu.HamamatsuAPI import DCAM
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class HamamatsuBase(CameraBase, SequenceDevice):
    """HamamatsuOrca camera class.

    This is the default parent class for Hamamatsu Cameras.
    This includes the ORCA Flash 4.0, Fusion, Lightning, and Fire.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize HamamatsuOrca class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
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
        self.camera_parameters["x_pixels_step"] = (
            self.camera_controller.step_image_width
        )
        self.camera_parameters["y_pixels_step"] = (
            self.camera_controller.step_image_height
        )
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
            else:
                self.camera_controller.set_property_value("readout_speed", 1)

        self.camera_parameters["pixel_size_in_microns"] = (
            self.camera_controller.get_property_value("pixel_width")
        )

        # Values are pulled from the CameraParameters section of the configuration.yml
        # file. Exposure time converted here from milliseconds to seconds.

        self.trigger_source = "Internal"

        self.set_trigger_mode()

        self.camera_parameters["supported_trigger_sources"] = ["External", "Internal", "Software"]
        self.camera_parameters["cooling"] = True

        cooling_state = self.camera_controller.get_property_value("cooling")
        self.configuration["experiment"]["CameraParameters"][self.microscope_name][
            "cooling"
        ] = ("On" if cooling_state == 2 else "Off")

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
        self.camera_controller.dev_close()
        # self.close_camera()

    @classmethod
    def connect(cls, camera_id: str) -> DCAM:
        """Connect to HamamatsuOrca camera.

        Parameters
        ----------
        camera_id : int
            Camera ID.

        Returns
        -------
        camera_controller : object
            Camera controller object.
        """
        camera_controller = DCAM(camera_id)
        return camera_controller

    @property
    def serial_number(self) -> str:
        """Get Camera Serial Number

        Returns
        -------
        serial_number : str
            Serial number for the camera.
        """
        return self.camera_controller._serial_number

    def report_settings(self) -> None:
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

    def close_camera(self) -> None:
        """Close HamamatsuOrca Camera"""
        self.camera_controller.dev_close()

    def set_trigger_mode(self, trigger_source: str = "External") -> None:
        """Set Hamamatsu trigger source and trigger mode.

        Parameters
        ----------
        trigger_source : str
            Trigger source: "External" or "Internal". Default is "External".
        """
        if trigger_source == "Software":
            self.trigger_source = "Software"
            # Standard trigger mode
            self.camera_controller.set_property_value("trigger_mode", 1)
            # Internal trigger.
            self.camera_controller.set_property_value("trigger_source", 3)
            logger.debug("Set camera trigger mode: Software Trigger.")

        elif trigger_source == "External":
            self.trigger_source = "External"
            self.camera_controller.set_property_value(
                "defect_correct_mode", self.camera_parameters["defect_correct_mode"]
            )
            self.camera_controller.set_property_value("trigger_active", 1.0)
            self.camera_controller.set_property_value("trigger_mode", 1)
            self.camera_controller.set_property_value("trigger_polarity", 2.0)
            self.camera_controller.set_property_value(
                "trigger_source", 2  # External trigger.
            )
            logger.debug("Set camera trigger mode: External Edge Trigger.")
        else:
            self.trigger_source = "Internal"
            # Standard trigger mode
            self.camera_controller.set_property_value("trigger_mode", 1)
            # Internal trigger.
            self.camera_controller.set_property_value("trigger_source", 1)
            logger.debug("Set camera trigger mode: Free running mode.")

    def set_sensor_mode(self, mode: str) -> None:
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
            self.camera_parameters["x_pixels_min"] = (
                self.camera_controller.min_image_width
            )
            self.camera_parameters["y_pixels_min"] = (
                self.camera_controller.min_image_height
            )
            self.camera_parameters["x_pixels_step"] = (
                self.camera_controller.step_image_width
            )
            self.camera_parameters["y_pixels_step"] = (
                self.camera_controller.step_image_height
            )
        else:
            print("Camera mode not supported")
            logger.debug("Camera mode not supported")

    def set_readout_direction(self, mode: str) -> None:
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

    def calculate_readout_time(self) -> float:
        """Get the duration of time needed to read out an image.

        Returns
        -------
        readout_time : float
            Duration of time needed to read out an image.
        """
        readout_time = self.camera_controller.get_property_value("readout_time")

        # with camera internal delay
        return readout_time  # + 4 * self.minimum_exposure_time

    def set_exposure_time(self, exposure_time: float) -> bool:
        """Set HamamatsuOrca exposure time.

        Note
        ----
            Units of the Hamamatsu API are in seconds.

        Parameters
        ----------
        exposure_time : float
            Exposure time in seconds.

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        return self.camera_controller.set_property_value("exposure_time", exposure_time)

    def set_line_interval(self, line_interval_time: float) -> bool:
        """Set HamamatsuOrca line interval.

        Parameters
        ----------
        line_interval_time : float
            Line interval duration.

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        return self.camera_controller.set_property_value(
            "internal_line_interval", line_interval_time
        )

    def get_line_interval(self) -> float:
        """Get HamamatsuOrca line interval.

        Returns
        -------
        line_interval_time : float
            Line interval duration.
        """
        line_interval = self.camera_controller.get_property_value(
            "internal_line_interval"
        )
        return line_interval

    def set_binning(self, binning_string: str) -> bool:
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

    def set_ROI(
        self,
        roi_width: int = 2048,
        roi_height: int = 2048,
        center_x: int = 1024,
        center_y: int = 1024,
    ) -> bool:
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

    def initialize_image_series(
        self, data_buffer: Optional[list] = None, number_of_frames: int = 100
    ) -> None:
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

    def close_image_series(self) -> None:
        """Close image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        self.camera_controller.stop_acquisition()
        self.is_acquiring = False

    def get_new_frame(self) -> list[int]:
        """Get frame from HamamatsuOrca camera.

        Returns
        -------
        frame_ids : list[int]
            Frame ids from HamamatsuOrca camera.
        """
        return self.camera_controller.get_frames()
    
    def generate_new_frame(self) -> None:
        if self.trigger_source == "Software":
            self.camera_controller.fire_software_trigger()

    def set_cooling(self, cooling: str) -> None:
        """Set camera cooling mode and temperature.

        Parameters
        ----------
        cooling : str
            'On' or 'Off'
        """
        if self.camera_parameters["cooling"] is False or cooling == "Off":
            self.camera_controller.set_property_value("cooling", 1)
            logger.info("Camera cooling turned Off.")
        # 1: "Off", 2: "On"
        elif cooling == "On":
            self.camera_controller.set_property_value("cooling", 2)
            logger.info(f"Camera cooling turned On.")

    def get_temperature(self) -> float:
        """Get camera cooling temperature.

        Returns
        -------
        temperature : float
            Camera cooling temperature in Celsius.
        """
        temperature = self.camera_controller.get_property_value("temperature")
        return temperature


@log_initialization
class HamamatsuOrcaLightningCamera(HamamatsuBase):
    """HamamatsuOrcaLightning camera class."""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize HamamatsuOrcaLightning class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        """
        HamamatsuBase.__init__(self, microscope_name, device_connection, configuration)

        self.camera_parameters["supported_readout_directions"] = ["Top-to-Bottom"]

        # self.minimum_exposure_time = 6.304 * 10 ** -6

    def __str__(self):
        """Return string representation of HamamatsuOrcaLightning class.

        Returns
        -------
        str
            String representation of HamamatsuOrcaLightning class.
        """
        return "HamamatsuOrcaLightning"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time: float, shutter_width: int
    ) -> tuple[float, float, float]:
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


@log_initialization
class HamamatsuOrcaFireCamera(HamamatsuBase):
    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize HamamatsuOrcaFire class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
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

    def __str__(self):
        """Return string representation of HamamatsuOrcaFire class.

        Returns
        -------
        str
            String representation of HamamatsuOrcaFire class.
        """
        return "HamamatsuOrcaFire"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time: float, shutter_width: int
    ) -> tuple[float, float, float]:
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


@log_initialization
class HamamatsuOrcaCamera(HamamatsuBase):
    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize HamamatsuOrca class.

        This is for controlling the Orca Flash 4.0.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        """
        HamamatsuBase.__init__(self, microscope_name, device_connection, configuration)

        self.camera_parameters["supported_readout_directions"] = [
            "Top-to-Bottom",
            "Bottom-to-Top",
        ]

        # self.minimum_exposure_time = 9.74436 * 10 ** -6

    def __str__(self):
        """Return string representation of HamamatsuOrca class.

        Returns
        -------
        str
            String representation of HamamatsuOrca class.
        """
        return "HamamatsuOrca"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time: float, shutter_width: int
    ) -> tuple[float, float, float]:
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


@log_initialization
class HamamatsuOrcaFusionCamera(HamamatsuBase):
    """HamamatsuOrcaFusion camera class."""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize HamamatsuOrcaFusion class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        """
        HamamatsuBase.__init__(self, microscope_name, device_connection, configuration)

        self.camera_parameters["supported_readout_directions"] = [
            "Top-to-Bottom",
            "Bottom-to-Top",
        ]

    def __str__(self):
        """Return string representation of HamamatsuOrcaFusion class.

        Returns
        -------
        str
            String representation of HamamatsuOrcaFusion class.
        """
        return "HamamatsuOrcaFusion"

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time: float, shutter_width: int
    ) -> tuple[float, float, float]:
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
