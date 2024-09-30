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

# Third Party Imports
import tifffile

# Local Imports
from navigate.config import get_navigate_path
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class CameraBase:
    """CameraBase - Parent camera class."""

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize CameraBase class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
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
        self.camera_parameters["trigger_source"] = 2.0
        self.camera_parameters["readout_speed"] = 1.0
        self.camera_parameters["pixel_size_in_microns"] = 6.5
        self.camera_parameters["trigger_active"] = 1.0
        self.camera_parameters["trigger_mode"] = 1.0
        self.camera_parameters["trigger_polarity"] = 2.0
        self.camera_parameters["supported_readout_directions"] = [
            "Top-to-Bottom",
            "Bottom-to-Top",
            "Bidirectional",
            "Rev. Bidirectional",
        ]

        # Initialize offset and variance maps, if present
        #: np.ndarray: Offset map
        #: np.ndarray: Variance map
        self._offset, self._variance = None, None
        self.get_offset_variance_maps()

    def __str__(self):
        """Return string representation of CameraBase."""
        return "CameraBase"

    def get_offset_variance_maps(self):
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
        try:
            map_path = os.path.join(get_navigate_path(), "camera_maps")
            self._offset = tifffile.imread(
                os.path.join(map_path, f"{serial_number}_off.tiff")
            )
            self._variance = tifffile.imread(
                os.path.join(map_path, f"{serial_number}_var.tiff")
            )
        except FileNotFoundError:
            logger.info(
                f"{str(self)}, Offset or variance map not found in {map_path}"
            )
            self._offset, self._variance = None, None
        return self._offset, self._variance

    @property
    def offset(self):
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
    def variance(self):
        """Return variance map. If not present, load from file.

        Returns
        -------
        variance : np.ndarray
            Variance map.
        """

        if self._variance is None:
            self.get_offset_variance_maps()
        return self._variance

    def set_readout_direction(self, mode):
        """Set HamamatsuOrca readout direction.

        Parameters
        ----------
        mode : str
            'Top-to-Bottom', 'Bottom-to-Top', 'bytrigger', or 'diverge'.
        """
        logger.info(f"Camera readout direction set to: {mode}.")

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
        full_chip_exposure time : float
            Full chip exposure time (s).
        """

        camera_line_interval = full_chip_exposure_time / (
            shutter_width + self.y_pixels - 1
        )

        self.camera_parameters["line_interval"] = camera_line_interval

        exposure_time = camera_line_interval * shutter_width
        return exposure_time, camera_line_interval, full_chip_exposure_time

    def close_camera(self):
        """Close camera."""
        pass

    def get_line_interval(self):
        """Return stored camera line interval.

        Returns
        -------
        line_interval : float
            line interval duration (s).
        """
        return self.camera_parameters.get("line_interval", None)
