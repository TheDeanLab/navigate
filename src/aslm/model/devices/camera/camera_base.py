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
import os

# Third Party Imports
import tifffile

# Local Imports
from aslm.config import get_aslm_path

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class CameraBase:
    """CameraBase Parent camera class.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    """

    def __init__(self, microscope_name, device_connection, configuration, id=0):
        if microscope_name not in configuration["configuration"]["microscopes"].keys():
            raise NameError(f"Microscope {microscope_name} does not exist!")

        self.camera_id = id
        self.configuration = configuration
        self.camera_controller = device_connection
        self.camera_parameters = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]
        self.is_acquiring = False

        print(f"\nIn CameraBase:: type(self.camera_parameters['hardware']) = {str(type(self.camera_parameters['hardware']))}\n")

        # Initialize Pixel Information
        self.pixel_size_in_microns = self.camera_parameters["pixel_size_in_microns"]
        self.binning_string = self.camera_parameters["binning"]
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])
        self.x_pixels = self.camera_parameters["x_pixels"]
        self.y_pixels = self.camera_parameters["y_pixels"]
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        # Initialize Exposure and Display Information - Convert from milliseconds
        # to seconds.
        self.camera_line_interval = self.camera_parameters["line_interval"]
        self.camera_exposure_time = self.camera_parameters["exposure_time"] / 1000
        self.camera_display_acquisition_subsampling = self.camera_parameters[
            "display_acquisition_subsampling"
        ]

        # Initialize offset and variance maps, if present
        self._offset, self._variance = None, None
        self.get_offset_variance_maps()

    def get_offset_variance_maps(self):
        if str(type(self.camera_parameters["hardware"])) == "<class 'multiprocessing.managers.ListProxy'>":
            serial_number = self.camera_parameters["hardware"][self.camera_id]["serial_number"]
        else:
            serial_number = self.camera_parameters["hardware"]["serial_number"]    
        try:
            map_path = os.path.join(get_aslm_path(), "camera_maps")
            self._offset = tifffile.imread(
                os.path.join(map_path, f"{serial_number}_off.tiff")
            )
            self._variance = tifffile.imread(
                os.path.join(map_path, f"{serial_number}_var.tiff")
            )
        except FileNotFoundError:
            self._offset, self._variance = None, None
        return self._offset, self._variance

    @property
    def offset(self):
        if self._offset is None:
            self.get_offset_variance_maps()
        return self._offset

    @property
    def variance(self):
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
        logger.debug(f"set camera readout direction to: {mode}")

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time, shutter_width
    ):
        """Convert normal mode exposure time to light-sheet mode exposure time.
        Calculate the parameters for an ASLM acquisition

        Parameters
        ----------
        full_chip_exposure_time : float
            Normal mode exposure time.
        shutter_width : int
            Width of ASLM rolling shutter.

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time (ms).
        camera_line_interval : float
            HamamatsuOrca line interval duration (s).
        """

        self.camera_line_interval = (full_chip_exposure_time / 1000) / (
            shutter_width + self.y_pixels + 10
        )
        exposure_time = self.camera_line_interval * shutter_width * 1000
        return exposure_time, self.camera_line_interval
