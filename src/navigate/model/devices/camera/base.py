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
import os
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

# Third Party Imports
import tifffile

# Local Imports
from navigate.config import get_navigate_path
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class CameraBase(ABC):
    """Abstract base class for cameras.

    This class provides the interface and common functionality for controlling
    cameras with navigate.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize CameraBase class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope

        Raises
        ------
        NameError
            If microscope name is not in configuration
        """
        if microscope_name not in configuration["configuration"]["microscopes"].keys():
            logger.error(f"Microscope {microscope_name} does not exist.")
            raise NameError(f"Microscope {microscope_name} does not exist.")

        #: str: Name of microscope in configuration
        self.microscope_name = microscope_name

        #: dict: Global configuration of the microscope
        self.configuration = configuration

        #: object: Hardware device to connect to
        self.camera_controller = device_connection

        #: dict: Camera parameters
        self.camera_parameters = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]

        #: bool: Whether the camera is currently acquiring
        self.is_acquiring = False

        # Initialize Pixel Information

        #: int: Minimum image width
        self.min_image_width = 4

        #: int: Minimum image height
        self.min_image_height = 4

        #: int: Minimum step size for image width.
        self.step_image_width = 4

        #: int: Minimum step size for image height.
        self.step_image_height = 4

        #: int: Number of pixels in the x direction
        self.x_pixels = 2048

        #: int: Number of pixels in the y direction
        self.y_pixels = 2048

        #: float: minimum exposure time
        self.minimum_exposure_time = 0.001
        self.camera_parameters["x_pixels"] = 2048
        self.camera_parameters["y_pixels"] = 2048
        # TODO: trigger_source, readout_speed,
        #  trigger_active, trigger_mode and trigger_polarity
        # can be removed after updating how we get the
        # readout time in model and controller
        self.camera_parameters["trigger_source"] = 2.0  # external trigger
        self.camera_parameters["readout_speed"] = 1.0
        self.camera_parameters["pixel_size_in_microns"] = 6.5
        self.camera_parameters["trigger_active"] = 1.0
        self.camera_parameters["trigger_mode"] = 1.0  # standard trigger mode
        self.camera_parameters["trigger_polarity"] = 2.0
        self.camera_parameters["supported_sensor_modes"] = ["Normal", "Light-Sheet"]
        self.camera_parameters["supported_readout_directions"] = [
            "Top-to-Bottom",
            "Bottom-to-Top",
            "Bidirectional",
            "Rev. Bidirectional",
        ]
        self.camera_parameters["supported_trigger_sources"] = ["External"]

        # Initialize offset and variance maps, if present
        #: np.ndarray: Offset map
        #: np.ndarray: Variance map
        self._offset, self._variance = None, None
        self.get_offset_variance_maps()

        #: bool: whether to use random images
        self.random_image = False

        #: int: current image id
        self.img_id = 0

        #: int: current tif id
        self.current_tif_id = 0

        #: list: list of tif images
        self.tif_images = []

        #: int: number of frames to load. Overwritten by synthetic_camera.
        self.num_of_frame = 100

    def __str__(self) -> str:
        """Return string representation of CameraBase."""
        return "CameraBase"

    @abstractmethod
    def get_new_frame(self) -> Any:
        """Get a new frame from the camera.

        This abstract method must be implemented by all subclasses.


        Returns
        -------
        frame : Any
            New frame from the camera.
        """
        pass

    @abstractmethod
    def initialize_image_series(self, data_buffer=None, number_of_frames=100) -> None:
        """Initialize image series.

        This abstract method must be implemented by all subclasses.

        Parameters
        ----------
        data_buffer :
            List of SharedNDArrays of shape=(self.img_height,
            self.img_width) and dtype="uint16"
            Default is None.
        number_of_frames : int
            Number of frames.  Default is 100.
        """
        pass

    @abstractmethod
    def close_image_series(self) -> None:
        """Close image series.

        This abstract method must be implemented by all subclasses.
        """
        pass

    @abstractmethod
    def set_line_interval(self, line_interval_time: float) -> None:
        """Set the camera line interval time.

        This abstract method must be implemented by all subclasses.
        """
        pass

    @abstractmethod
    def set_exposure_time(self, exposure_time: float) -> None:
        """Set the camera exposure time."""
        pass

    def load_images(self, filenames: Optional[str] = None, ds=None) -> None:
        """Pre-populate the buffer with images. Can either come from TIFF files or
        Numpy stacks.

        Parameters
        ----------
        filenames : str, optional
            List of TIFF filenames, by default None
        ds : list, optional
            List of Numpy stacks, by default None

        Raises
        ------
        tifffile.TiffFileError
            If the TIFF file cannot be opened.
        """
        self.random_image = False
        self.img_id = 0
        self.current_tif_id = 0
        self.tif_images = []
        idx = 0
        if filenames is not None:
            # Load TIFF file into buffer as slices
            for image_file in filenames:
                try:
                    tif = tifffile.TiffFile(image_file)
                    if len(tif.pages) == 1:
                        self.tif_images.append([tif.asarray()])
                    else:
                        self.tif_images.append(tif.asarray())
                    idx += len(tif.pages)

                    # TODO: self.num_of_frame is not defined in the base class
                    if idx >= self.num_of_frame:
                        return
                except tifffile.TiffFileError:
                    pass
        elif ds is not None:
            # Load a Numpy stack into buffer as slices
            # Assume the stack is in the order ZYX
            for idx, data in enumerate(ds):
                self.tif_images.append(data)
                idx += len(data)
                if idx >= self.num_of_frame:
                    return
        else:
            self.random_image = True

    def get_offset_variance_maps(self) -> Any:
        """Get offset and variance maps from file.

        Returns
        -------
        offset : np.ndarray
            Offset map.
        variance : np.ndarray
            Variance map.

        Raises
        ------
        FileNotFoundError
            If offset or variance map is not found.
        """
        serial_number = self.camera_parameters["hardware"]["serial_number"]
        map_path = os.path.join(get_navigate_path(), "camera_maps")
        try:
            self._offset = tifffile.imread(
                os.path.join(map_path, f"{serial_number}_off.tiff")
            )
            self._variance = tifffile.imread(
                os.path.join(map_path, f"{serial_number}_var.tiff")
            )
        except FileNotFoundError:
            logger.info(f"{str(self)}, Offset or variance map not found in {map_path}")
            self._offset, self._variance = None, None
        return self._offset, self._variance

    @property
    def offset(self) -> Any:
        """Return offset map. If not present, load from file.

        Returns
        -------
        offset : np.ndarray
            Offset map.
        """
        if self._offset is None:
            self.get_offset_variance_maps()
        return self._offset

    @property
    def variance(self) -> Any:
        """Return variance map. If not present, load from file.

        Returns
        -------
        variance : np.ndarray
            Variance map.
        """

        if self._variance is None:
            self.get_offset_variance_maps()
        return self._variance

    def set_readout_direction(self, mode: str) -> None:
        """Set HamamatsuOrca readout direction.

        Parameters
        ----------
        mode : str
            'Top-to-Bottom', 'Bottom-to-Top', 'bytrigger', or 'diverge'.
        """
        logger.info(f"Camera readout direction set to: {mode}.")

    @abstractmethod
    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time: float, shutter_width: float
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
        full_chip_exposure time : float
            Full chip exposure time (s).
        """

        camera_line_interval = full_chip_exposure_time / (
            shutter_width + self.y_pixels - 1
        )

        self.camera_parameters["line_interval"] = camera_line_interval

        exposure_time = camera_line_interval * shutter_width
        return exposure_time, camera_line_interval, full_chip_exposure_time

    def close_camera(self) -> None:
        """Close camera."""
        pass

    def get_line_interval(self) -> float:
        """Return stored camera line interval.

        Returns
        -------
        line_interval : float
            line interval duration (s).
        """
        return self.camera_parameters.get("line_interval", None)

    def set_ROI_and_binning(
        self,
        roi_width: int = 2048,
        roi_height: int = 2048,
        center_x: int = 1024,
        center_y: int = 1024,
        binning: str = "1x1",
    ) -> bool:
        """Change the size of the active region on the camera and set the binning mode.

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
        binning : str
            Desired binning properties (e.g., '1x1', '2x2', '4x4', '8x8', '16x16',
            '1x2', '2x4')

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        # Set ROI
        result = self.set_ROI(roi_width, roi_height, center_x, center_y)
        if not result:
            return False

        # Set Binning
        result = self.set_binning(binning)
        return result

    @abstractmethod
    def set_trigger_mode(self, trigger_source: str = "External") -> None:
        """Set the camera trigger source to external or internal free run mode.

        This abstract method must be implemented by all subclasses.

        Parameters
        ----------
        trigger_source : str
            Trigger source. Options are 'External' or 'Internal'.
        """
        pass
