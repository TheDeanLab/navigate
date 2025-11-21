# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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

# ################################################################################
# WARNING:
#    This camera class has not been internally tested by our team.
#    Users are advised to exercise caution when using it.
# NOTE:
#    This module depends on Daheng's proprietary 'gxipy' SDK.
#    To use this camera class, 'gxipy' must be installed manually.
#    See the ImportError message below for installation instructions.
# .   The Line0 trigger input is used by default for external triggering.
# ################################################################################

# Standard Library Imports
import logging
from typing import Union, Any, List

# Third Party Imports
try:
    import gxipy as gx
except ImportError:
    raise ImportError(
        "Missing required module 'gxipy'.\n"
        "This is Daheng Imaging's proprietary Python SDK and must be installed manually.\n\n"
        "-> Download the SDK from: https://www.daheng-imaging.com/\n"
        "-> Locate 'gxipy' under: Development/Samples/Python/gxipy\n"
        "-> Then install it using pip:\n"
        "   pip install /full/path/to/gxipy\n\n"
        "See Navigate’s documentation for more details if available."
    )

import numpy as np

# Local Imports
from navigate.model.utils.exceptions import UserVisibleException
from navigate.model.devices.camera.base import CameraBase
from navigate.tools.decorators import log_initialization


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class DahengCamera(CameraBase):
    """
    Daheng camera implementation for the MER2-1220-32U3C model.

    This class provides initialization, streaming, and configuration
    methods for this specific model using the gxipy SDK.
    """

    def __init__(self, microscope_name, device_connection, configuration):
        """
        Initialize the camera with given configuration.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope this camera is associated with.
        device_connection : gxipy.Device
            A connected Daheng device handle, returned from DahengCamera.connect().
            Required for all SDK interaction. Included here to match Navigate's expected interface.
        configuration : dict
            Device configuration settings (e.g. resolution, exposure).
        """
        super().__init__(microscope_name, device_connection, configuration)

        self.microscope_name = microscope_name
        self.device_connection = (
            device_connection  # Store raw connection for compatibility
        )
        self.configuration = configuration

        # Daheng device handles
        self.device = device_connection  # The camera device object, returned from connect(). Required for all SDK interaction.
        self.feature_control = None  # Feature control interface. Used to get/set camera features (exposure, ROI, trigger, etc.).
        self.data_stream = None  # Data stream object. Handles image streaming and retrieval from the camera buffer.
        self.device_serial_number = None
        self.payload_size = None
        self.is_connected = False

        # Camera config parameters
        self.camera_parameters = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]
        self.camera_parameters["x_pixels"] = (
            2048  # Placeholder until real values are known
        )
        self.camera_parameters["y_pixels"] = 2048

        # Acquisition state
        self.is_acquiring = False
        self._data_buffer = None
        self._number_of_frames = 100
        self._frames_received = 0
        self._frame_ids = []
        self._exposure_time = 0.05  # Seconds
        self._scan_mode = 0
        self._scan_delay = 0

        # Binning
        self.x_binning = None
        self.y_binning = None

        # Finish hardware setup (initialize feature_control etc.)
        self.initialize_sdk_state()

        self.camera_parameters["supported_readout_directions"] = ["Top-to-Bottom"]
        self.camera_parameters["supported_trigger_sources"] = ["External"]
        # support Normal and Light-Sheet modes
        self.camera_parameters["supported_sensor_modes"] = ["Normal", "Light-Sheet"]

    def __str__(self) -> str:
        """
        Return a human-readable string representation of the camera status.

        Returns
        -------
        str
            Status string including serial number and connection state.
        """
        status = "Connected" if getattr(self, "is_connected", False) else "Disconnected"
        serial = getattr(self, "device_serial_number", "N/A")
        return f"MER2_1220_32U3C Camera [Serial: {serial}, Status: {status}]"

    def __del__(self) -> None:
        """
        Destructor for the DahengCamera object.

        Ensures that the camera is cleanly disconnected when the object is deleted.
        Logs any exception that occurs during cleanup without raising it.
        """
        try:
            self.disconnect()
        except Exception as e:
            logger.debug(f"Exception in DahengCamera.__del__: {e}")

    @classmethod
    def get_connect_params(cls) -> list:
        """
        Return the list of required parameters for camera connection.

        Returns
        -------
        list
            An empty list since no parameters are required for Daheng connection.
        """
        return ["serial_number"]

    @classmethod
    def connect(cls, serial_number: str = None) -> gx.Device:
        """
        Connect to a Daheng camera using the gxipy SDK.

        Parameters
        ----------
        serial_number : str, optional
            The serial number of the desired camera. If None, the default camera
            (index 1) is used.

        Returns
        -------
        device : gxipy.Device
            An open device object for the selected camera.

        Raises
        ------
        UserVisibleException
            If no camera is found, or if the specified serial number does not match any camera.
        """
        # Discover and list available devices using the Daheng SDK
        device_manager = gx.DeviceManager()
        device_manager.update_device_list()
        dev_info_list = device_manager.get_device_list()

        # Raise error if no cameras are detected
        if not dev_info_list:
            raise UserVisibleException("No Daheng camera found.")

        # Try to match serial number if provided
        if serial_number:
            for i, dev_info in enumerate(dev_info_list):
                if dev_info.get("sn") == serial_number:
                    device = device_manager.open_device_by_index(i)
                    break
            else:
                raise UserVisibleException(
                    f"Daheng camera with serial {serial_number} not found."
                )
        else:
            # Default: connect to the first available camera (index 1 due to C-style in gxipy)
            device = device_manager.open_device_by_index(1)

        return device

    def initialize_sdk_state(self) -> None:
        """
        Finalize Daheng SDK setup using the already opened device.

        This method retrieves the feature control and data stream handles,
        sets basic acquisition mode, and extracts initial configuration
        like serial number and sensor resolution.

        Raises
        ------
        UserVisibleException
            If the camera device handle is missing or SDK initialization fails.
        """
        if self.device is None:
            raise UserVisibleException(
                "Daheng device handle not set. Was connect() called?"
            )

        self.is_connected = True

        try:
            # Get feature control interface and data stream object
            self.feature_control = self.device.get_remote_device_feature_control()
            self.data_stream = self.device.data_stream

            # Get static device properties
            self.device_serial_number = self.feature_control.get_string_feature(
                "DeviceSerialNumber"
            ).get()
            self.payload_size = self.feature_control.get_int_feature(
                "PayloadSize"
            ).get()

            # Configure Acquisition and Trigger defaults
            # Line0 as default trigger source
            self.set_trigger_source("LINE0")
            # Trigger mode ON by default
            self.set_camera_trigger_mode("ON")
            # trigger polarity is rising edge by default
            self.device.TriggerActivation.set(gx.GxTriggerActivationEntry.RISINGEDGE)
            # Set acquisition mode to single frame
            self.device.AcquisitionMode.set(gx.GxAcquisitionModeEntry.CONTINUOUS)
            # Set trigger mode to FrameStart
            self.device.TriggerSelector.set(gx.GxTriggerSelectorEntry.FRAMESTART)
            # set trigger delay to 0
            self.device.TriggerDelay.set(0.0)
            # Set Exposure Mode to Timed
            self.device.ExposureMode.set(gx.GxExposureModeEntry.TIMED)

            # Get current image dimensions from hardware
            width = self.feature_control.get_int_feature("Width").get()
            height = self.feature_control.get_int_feature("Height").get()

            configured_x = self.camera_parameters.get("x_pixels")
            configured_y = self.camera_parameters.get("y_pixels")

            if configured_x != width or configured_y != height:
                logger.info(
                    f"Configured resolution ({configured_x}x{configured_y}) differs from hardware ({width}x{height}). "
                    "Overriding with hardware values."
                )

            # Save into internal state and config dictionary
            self.camera_parameters["x_pixels"] = width
            self.camera_parameters["y_pixels"] = height
            self.x_pixels = width
            self.y_pixels = height

            logger.info(
                f"Daheng camera connected: Serial={self.device_serial_number}, "
                f"Resolution={width}x{height}"
            )

        except Exception as e:
            raise UserVisibleException(f"Failed to initialize camera SDK state: {e}")

    @property
    def serial_number(self) -> str:
        """
        Return the serial number of the connected camera.

        Returns
        -------
        str
            Serial number of the camera, or "UNKNOWN" if the camera is not connected.
        """
        if not self.is_connected or self.device_serial_number is None:
            logger.warning(
                "Attempted to retrieve serial number, but camera is not connected."
            )
            return "UNKNOWN"

        return self.device_serial_number

    def report_settings(self) -> None:
        """
        Log the current camera settings using the Daheng SDK.

        This includes sensor dimensions, binning, exposure time,
        and trigger configuration.

        If the camera is not connected, a warning is logged instead.
        """
        if not self.is_connected:
            logger.warning("Camera not connected.")
            return

        try:
            # Retrieve current settings from camera hardware
            sensor_mode = self.device.SensorShutterMode.get()
            sensor_width = self.feature_control.get_int_feature("Width").get()
            sensor_height = self.feature_control.get_int_feature("Height").get()
            bin_x = self.feature_control.get_int_feature("BinningHorizontal").get()
            bin_y = self.feature_control.get_int_feature("BinningVertical").get()
            exposure_us = self.feature_control.get_float_feature("ExposureTime").get()
            trigger_mode = self.feature_control.get_enum_feature("TriggerMode").get()
            trigger_source = self.feature_control.get_enum_feature(
                "TriggerSource"
            ).get()

            # Log all settings
            logger.info("Camera Settings:")
            logger.info(f"  sensor_mode: {sensor_mode} (0: Normal, 1: Light-Sheet)")
            logger.info(f"  binning: {bin_x}x{bin_y}")
            logger.info("  readout_speed: N/A")
            logger.info("  trigger_active: N/A")
            logger.info(f"  trigger_mode: {trigger_mode}")
            logger.info("  trigger_polarity: N/A")
            logger.info(f"  trigger_source: {trigger_source}")
            logger.info("  internal_line_interval: N/A")
            logger.info(f"  sensor size: {sensor_width}x{sensor_height}")
            logger.info(f"  image height and width: {self.x_pixels}x{self.y_pixels}")
            logger.info(f"  exposure_time: {exposure_us / 1_000_000:.6f} seconds")

        except Exception as e:
            logger.warning(f"Failed to read camera settings: {e}")

    def disconnect(self) -> None:
        """
        Disconnect from the Daheng camera and clean up internal state.

        This method safely closes the device connection and clears
        all associated resources, even if errors occur during shutdown.
        """
        # Reset associated handles and status flags
        self.feature_control = None  # release device handler
        self.data_stream = None
        self.device_serial_number = None
        self.payload_size = None
        self.is_connected = False

        if self.device is not None:
            try:
                # Attempt to close the hardware connection
                self.device.close_device()
            except Exception as e:
                logger.warning(f"Error while closing Daheng device: {e}")
            finally:
                self.device = None

        logger.info("Daheng camera disconnected and internal state cleared.")

    def set_sensor_mode(self, mode: str) -> None:
        """
        Stub method for setting sensor mode - not supported on Daheng cameras.

        Parameters
        ----------
        mode : str
            Requested sensor mode (e.g., 'Normal', 'Light-Sheet').
            This value is ignored as Daheng does not support sensor mode switching.
        """
        modes_dict = {"Normal": 0, "Light-Sheet": 1}

        self._scan_mode = modes_dict.get(mode, 0)
        self.device.SensorShutterMode.set(self._scan_mode)

        logger.debug(f"Sensor mode set to {mode} ({self._scan_mode})")

    def set_readout_direction(self, mode: str) -> None:
        """
        Stub method for setting readout direction — not supported on Daheng cameras.

        Parameters
        ----------
        mode : str
            Desired readout direction (e.g., 'Top-to-Bottom', 'Bottom-to-Top', 'Alternate').
            This value is ignored as Daheng does not support changing readout direction.
        """
        logger.warning(
            f"Readout direction '{mode}' is not supported on Daheng cameras."
        )

    def calculate_readout_time(self) -> float:
        """
        Stub method for readout time calculation — not supported by Daheng cameras.

        Returns
        -------
        float
            Always returns 0, as Daheng does not expose readout timing data.
        """
        logger.warning(
            "DahengCamera does not support readout time calculation. Returning 0."
        )
        return 0

    def set_line_interval(self, line_interval_time: float) -> bool:
        """
        Stub for line interval (scan delay) — not supported by Daheng cameras.

        Parameters
        ----------
        line_interval_time : float
            Requested interval between sensor lines (ignored).

        Notes
        -----
        This method is included for compatibility. No action is performed.
        """
        logger.warning("set_line_interval is not supported by Daheng cameras.")

        # Set internal scan delay to zero for compatibility tracking
        self._scan_delay = 0

        return False

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time: float, shutter_width: int
    ) -> tuple[float, float, float]:
        """
        Stub for light-sheet exposure time calculation — not supported on Daheng cameras.

        Parameters
        ----------
        full_chip_exposure_time : float
            Normal mode exposure time (ignored).
        shutter_width : int
            Width of the light sheet in pixels (ignored).

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time (s).
        camera_line_interval : float
            HamamatsuOrca line interval duration (s).
        full_chip_exposure time : float
            Full chip exposure time (s).
        """
        return full_chip_exposure_time, 0, full_chip_exposure_time

    def set_exposure_time(self, exposure_time: float) -> None:
        """
        Set the camera exposure time.

        Parameters
        ----------
        exposure_time : float
            Desired exposure time in seconds.

        Raises
        ------
        UserVisibleException
            If the camera is not connected or the exposure time cannot be set.
        """
        if not self.is_connected:
            raise UserVisibleException("Camera must be connected to set exposure time.")

        try:
            # Convert seconds to microseconds as required by gxipy
            exposure_time_us = int(exposure_time * 1_000_000)

            if self._scan_mode == 1:
                exposure_time_us = exposure_time_us // self.y_pixels
                self.camera_parameters["line_interval"] = exposure_time_us / 1_000_000
                logger.debug(
                    f"Light-Sheet mode: Adjusted exposure time to {exposure_time_us} µs based on {self.y_pixels} lines"
                )

            # Send exposure time setting to the camera
            self.feature_control.get_float_feature("ExposureTime").set(exposure_time_us)

            # Cache it internally for convenience
            self._exposure_time = exposure_time

            logger.info(f"Exposure time set to {exposure_time_us} µs")

        except Exception as e:
            raise UserVisibleException(f"Failed to set exposure time: {e}")

    def set_gain(self, gain: float) -> None:
        """
        Set the analog gain for the camera.

        Parameters
        ----------
        gain : float
            Desired gain value in decibels (dB). The range depends on the specific camera model.

        Raises
        ------
        UserVisibleException
            If the camera is not connected or gain setting fails.
        """
        if not self.is_connected:
            raise UserVisibleException("Camera must be connected to set gain.")

        try:
            # Set gain using the Daheng SDK float feature
            self.feature_control.get_float_feature("Gain").set(gain)

            logger.info(f"Gain set to {gain} dB")

        except Exception as e:
            raise UserVisibleException(f"Failed to set gain: {e}")

    def set_binning(self, binning_string: str = "1x1") -> bool:
        """
        Set Daheng binning mode.

        Parameters
        ----------
        binning_string : str, optional
            Desired binning (e.g. '1x1', '2x2', '4x4').
            Defaults to '1x1' (no binning).

        Returns
        -------
        bool
            True if binning was set successfully, False otherwise.
        """
        if not self.is_connected:
            raise UserVisibleException("Camera must be connected to set binning.")

        try:
            # Parse input
            idx = binning_string.index("x")
            bin_x = int(binning_string[:idx])
            bin_y = int(binning_string[idx + 1 :])

            # Apply the changes to the hardware
            self.feature_control.get_int_feature("BinningHorizontal").set(bin_x)
            self.feature_control.get_int_feature("BinningVertical").set(bin_y)

            # Update internal binning variables accordingly
            self.x_binning = bin_x
            self.y_binning = bin_y

            # Update resolution info
            width = self.feature_control.get_int_feature("Width").get()
            height = self.feature_control.get_int_feature("Height").get()
            self.x_pixels = int(width / bin_x)
            self.y_pixels = int(height / bin_y)

            logger.info(
                f"Binning set to {binning_string} (effective resolution {self.x_pixels}x{self.y_pixels})"
            )
            return True

        except Exception as e:
            logger.warning(f"Failed to set binning to {binning_string}: {e}")
            return False

    def set_ROI(
        self, roi_width=2048, roi_height=2048, center_x=1024, center_y=1024
    ) -> bool:
        """
        Set the region of interest (ROI) on the sensor, centered at (center_x, center_y).

        Parameters
        ----------
        roi_width : int
            Width of active camera region.
        roi_height : int
            Height of active camera region.
        center_x : int
            X position of the ROI center.
        center_y : int
            Y position of the ROI center.

        Returns
        -------
        bool
            True if ROI was set successfully, False otherwise.
        """
        if not self.is_connected:
            raise UserVisibleException("Camera must be connected to set ROI.")

        # Get full sensor dimensions from config (not from current ROI)
        full_width = self.camera_parameters["x_pixels"]
        full_height = self.camera_parameters["y_pixels"]

        # Validate ROI size
        if (
            roi_width > full_width
            or roi_height > full_height
            or roi_width < 1
            or roi_height < 1
            or roi_width % 2 != 0
            or roi_height % 2 != 0
        ):
            logger.warning(f"Invalid ROI dimensions: {roi_width}x{roi_height}")
            return False

        # Compute top-left corner from center
        offset_x = center_x - roi_width // 2
        offset_y = center_y - roi_height // 2

        if offset_x < 0 or offset_y < 0:
            logger.warning(
                f"Computed ROI offset out of bounds: x={offset_x}, y={offset_y}"
            )
            return False

        try:
            # Apply ROI settings to hardware
            self.feature_control.get_int_feature("OffsetX").set(offset_x)
            self.feature_control.get_int_feature("OffsetY").set(offset_y)
            self.feature_control.get_int_feature("Width").set(roi_width)
            self.feature_control.get_int_feature("Height").set(roi_height)

            # Update internal state
            self.x_pixels = roi_width
            self.y_pixels = roi_height

            logger.info(
                f"ROI set to (offset_x={offset_x}, offset_y={offset_y}, width={roi_width}, height={roi_height})"
            )
            return True

        except Exception as e:
            logger.warning(f"Failed to set ROI: {e}")
            return False

    def initialize_image_series(self, data_buffer=None, number_of_frames=100) -> None:
        """
        Prepare for multi-frame acquisition (e.g. a stack).

        Parameters
        ----------
        data_buffer : list of SharedNDArrays or None
            External buffer for storing acquired images.
        number_of_frames : int
            Total number of frames to acquire.
        """
        self._data_buffer = data_buffer
        self._number_of_frames = number_of_frames
        self._frames_received = 0
        self._frame_ids = []
        self.is_acquiring = True

        self.start_acquisition()

        logger.debug(f"Initialized image series: {number_of_frames} frames")

    def get_new_frame(self) -> List[int]:
        """
        Retrieve a new image frame and return its index in the internal buffer.

        Returns
        -------
        List[int]
            A single-element list containing the index of the received frame
            in the buffer. Returns an empty list if no image was received
            or an error occurred.

        Notes
        -----
        This method returns a list (rather than a plain int or None)
        for compatibility with other camera classes in Navigate that
        may return multiple frame indices (e.g., burst modes).
        """
        try:
            raw_image = self.data_stream.snap_image(1000)  # Wait up to 1000 ms
            if raw_image is None:
                logger.warning("No image received from camera.")
                return []

            self._data_buffer[self._frames_received][:, :] = raw_image.get_numpy_array()
            frame_to_return = [self._frames_received]
            self._frames_received += 1

            # Make the buffer circular – wrap around when full
            if self._frames_received >= self._number_of_frames:
                self._frames_received = 0

            return frame_to_return

        except Exception as e:
            logger.error(f"Image receive failed: {e}")
            return []

    def close_image_series(self) -> None:
        """
        Stop multi-frame acquisition and mark acquisition as complete.
        """
        self.stop_acquisition()
        self.is_acquiring = False
        self._data_buffer = None

    def start_acquisition(self) -> None:
        """
        Start image acquisition on the camera.

        This method enables the data stream and issues the acquisition start command
        using the Daheng SDK. It also logs the current acquisition settings for debugging.

        Raises
        ------
        UserVisibleException
            If the camera is not connected or if acquisition start fails.
        """
        if not self.is_connected:
            raise UserVisibleException(
                "Camera must be connected before starting acquisition."
            )

        try:
            # Start the image data stream (necessary for frame delivery)
            self.data_stream.start_stream()

            # Send the acquisition start command to the camera
            self.feature_control.get_command_feature("AcquisitionStart").send_command()

            # Retrieve and log current acquisition settings
            acq_mode = (
                self.feature_control.get_enum_feature("AcquisitionMode")
                .get_current_entry()
                .get_symbolic()
            )
            trigger_mode = (
                self.feature_control.get_enum_feature("TriggerMode")
                .get_current_entry()
                .get_symbolic()
            )
            trigger_source = (
                self.feature_control.get_enum_feature("TriggerSource")
                .get_current_entry()
                .get_symbolic()
            )

            logger.info(
                f"Acquisition started: "
                f"AcquisitionMode={acq_mode}, "
                f"TriggerMode={trigger_mode}, "
                f"TriggerSource={trigger_source}"
            )

        except Exception as e:
            raise UserVisibleException(f"Failed to start acquisition: {e}")

    def stop_acquisition(self) -> None:
        """
        Stop image acquisition and flush camera buffers.

        This method issues a stop command to the camera and halts the data stream.
        It is safe to call this even if acquisition was not running.

        Raises
        ------
        UserVisibleException
            If stopping the acquisition fails while the camera is connected.
        """
        if not self.is_connected:
            logger.warning("Attempted to stop acquisition, but camera is not connected")
            return

        try:
            # Stop the hardware and the data stream
            self.feature_control.get_command_feature("AcquisitionStop").send_command()
            self.data_stream.stop_stream()

            self.is_acquiring = False
            logger.info("Acquisition stopped")

        except Exception as e:
            raise UserVisibleException(f"Failed to stop acquisition: {e}")

    def set_camera_trigger_mode(self, mode: str) -> None:
        """
        Set the trigger mode on the camera.

        Parameters
        ----------
        mode : str
            Must be a valid enum entry for the TriggerMode feature, typically 'ON' or 'OFF'.

        Raises
        ------
        UserVisibleException
            If the camera is not connected or the trigger mode cannot be set.
        """
        if not self.is_connected:
            raise UserVisibleException("Camera must be connected to set trigger mode")

        try:
            # Set the trigger mode using the Daheng SDK enum feature
            self.feature_control.get_enum_feature("TriggerMode").set(mode)
            logger.info(f"Trigger mode set to {mode}")

        except Exception as e:
            raise UserVisibleException(f"Failed to set trigger mode to '{mode}': {e}")

    def set_trigger_mode(self, trigger_source="External"):
        """Set the camera trigger source to external or internal free run mode.

        This abstract method must be implemented by all subclasses.

        Parameters
        ----------
        trigger_source : str
            Trigger source. Options are 'External' or 'Internal'.
        """
        super().set_trigger_mode(trigger_source)

    def set_trigger_source(self, source: str) -> None:
        """
        Set the trigger source on the camera.

        Parameters
        ----------
        source : str
            Trigger source (e.g., 'SOFTWARE', 'LINE0', 'LINE1', 'LINE2', 'LINE3').

        Raises
        ------
        UserVisibleException
            If the camera is not connected or the trigger source cannot be set.
        """
        if not self.is_connected:
            raise UserVisibleException("Camera must be connected to set trigger source")

        try:
            # Set the trigger source using the Daheng SDK enum feature
            self.feature_control.get_enum_feature("TriggerSource").set(source)

            logger.info(f"Trigger source set to {source}")

        except Exception as e:
            raise UserVisibleException(
                f"Failed to set trigger source to '{source}': {e}"
            )

    def send_software_trigger(self) -> None:
        """
        Send a software trigger to the camera.

        Raises
        ------
        UserVisibleException
            If the camera is not connected or the trigger command fails.
        """
        if not self.is_connected:
            raise UserVisibleException(
                "Camera must be connected to send a software trigger"
            )

        try:
            self.feature_control.get_command_feature("TriggerSoftware").send_command()
            logger.debug("Software trigger sent")
        except Exception as e:
            raise UserVisibleException(
                "Failed to send software trigger. Make sure trigger mode is set to 'ON' "
                "and trigger source is set to 'SOFTWARE'.\n"
                f"Original error: {e}"
            )

    def snap_software_triggered(self, timeout_ms: int = 1000) -> Union[np.ndarray, Any]:
        """
        Send a software trigger and return the resulting image.

        This requires the trigger mode to be 'ON' and the trigger source to be 'SOFTWARE'.

        Parameters
        ----------
        timeout_ms : int, optional
            Timeout in milliseconds to wait for the image (default is 1000 ms).

        Returns
        -------
        np.ndarray
            The acquired image as a NumPy array.

        Raises
        ------
        UserVisibleException
            If the camera is not connected or trigger settings are incorrect.
        """
        if not self.is_connected:
            raise UserVisibleException(
                "Camera must be connected to perform a software-triggered snap"
            )

        # Get the current trigger mode and source to see that they are correct
        trigger_mode = (
            self.feature_control.get_enum_feature("TriggerMode")
            .get_current_entry()
            .get_symbolic()
        )
        trigger_source = (
            self.feature_control.get_enum_feature("TriggerSource")
            .get_current_entry()
            .get_symbolic()
        )

        if not (trigger_mode == "ON" and trigger_source == "SOFTWARE"):
            raise UserVisibleException(
                "Software-triggered snapping requires TriggerMode='ON' and TriggerSource='SOFTWARE'"
            )

        self.send_software_trigger()
        return self.snap_image(timeout_ms=timeout_ms)

    def snap_image(
        self, timeout_ms: int = 1000, return_raw: bool = False
    ) -> Union[np.ndarray, Any]:
        """
        Retrieve the next image from the camera buffer.

        This method waits for the next available frame. If 'return_raw' is True, the raw gxipy
        image object is returned instead of a NumPy array.

        Parameters
        ----------
        timeout_ms : int, optional
            Timeout in milliseconds to wait for an image (default is 1000).
        return_raw : bool, optional
            If True, returns a gxipy.RawImage object.
            If False (default), returns the image as a NumPy array using RawImage.get_numpy_array().

        Returns
        -------
        np.ndarray or gxipy.RawImage
            The acquired image, either as a NumPy array or the raw gxipy image.

        Raises
        ------
        UserVisibleException
            If the camera is not connected or no image is received within the timeout.
        """
        if not self.is_connected:
            raise UserVisibleException("Camera must be connected to retrieve an image")

        try:
            raw_image = self.data_stream.snap_image(timeout_ms)
            if raw_image is None:
                raise UserVisibleException(
                    "No image received from the camera (timeout or stream failure)"
                )

            return raw_image if return_raw else raw_image.get_numpy_array()

        except Exception as e:
            raise UserVisibleException(f"Error retrieving image from camera: {e}")
