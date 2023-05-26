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
import time
import ctypes

# Third Party Imports
import numpy as np
from tifffile import TiffFile, TiffFileError

# Local Imports
from aslm.model.analysis import camera
from aslm.model.devices.camera.camera_base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticCameraController:
    """SyntheticCameraController. Synthetic Camera API."""

    def __init__(self):
        pass

    def get_property_value(self, name):
        """Provides the idprop value after looking it up in the property_dict

        Parameters
        ----------
        name : str
            Not currently used.

        Returns
        -------
        property_value : int
            Currently hard-coded to -1.
        """
        return -1

    def set_property_value(self, name, value):
        logger.debug(f"set camera property {name}: {value}")


class SyntheticCamera(CameraBase):
    """SyntheticCamera camera class.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope

    """

    def __init__(self, microscope_name, device_connection, configuration):
        super().__init__(microscope_name, device_connection, configuration)

        self.is_acquiring = False
        self._mean_background_count = 100
        self._noise_sigma = camera.compute_noise_sigma()
        self.current_frame_idx = None
        self.data_buffer = None
        self.num_of_frame = None
        self.pre_frame_idx = None
        self.random_image = True
        self.serial_number = "synthetic"

        logger.info("SyntheticCamera Class Initialized")

    def __del__(self):
        logger.info("SyntheticCamera Shutdown")
        pass

    def report_settings(self):
        """Print Camera Settings."""
        pass

    def close_camera(self):
        """Close SyntheticCamera Camera"""
        pass

    def set_sensor_mode(self, mode):
        """Set SyntheticCamera sensor mode.

        Parameters
        ----------
        mode : str
            'Normal' or 'Light-Sheet'
        """
        pass

    def set_exposure_time(self, exposure_time):
        """Set SyntheticCamera exposure time.

        All of our units are in milliseconds. Function convert to seconds.

        Parameters
        ----------
        exposure_time : float
            Exposure time in milliseconds.

        """
        self.camera_exposure_time = exposure_time / 1000

    def set_line_interval(self, line_interval_time):
        """Set SyntheticCamera line interval.

        Parameters
        ----------
        line_interval_time : float
            Line interval duration.
        """
        pass

    def set_binning(self, binning_string):
        """Set SyntheticCamera binning mode.

        Parameters
        ----------
        binning_string : str
            Desired binning properties (e.g., '2x2', '4x4', '8x8'
        """
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        """Initialize SyntheticCamera image series.

        Parameters
        ----------
        data_buffer : int
            Size of the data to buffer.  Default is None.
        number_of_frames : int
            Number of frames.  Default is 100.
        """
        self.data_buffer = data_buffer
        self.num_of_frame = number_of_frames
        self.current_frame_idx = 0
        self.pre_frame_idx = 0
        self.is_acquiring = True

    def close_image_series(self):
        """Close image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        self.pre_frame_idx = 0
        self.current_frame_idx = 0
        self.is_acquiring = False

    def load_images(self, filenames=None, ds=None):
        """Pre-populate the buffer with images. Can either come from TIFF files or
        Numpy stacks."""
        self.random_image = False
        self.img_id = 0
        self.current_tif_id = 0
        self.tif_images = []
        idx = 0
        if filenames is not None:
            # Load TIFF file into buffer as slices
            for image_file in filenames:
                try:
                    tif = TiffFile(image_file)
                    self.tif_images.append(tif.asarray())
                    idx += len(tif.pages)
                    if idx >= self.num_of_frame:
                        return
                except TiffFileError:
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

    def generate_new_frame(self):
        """Generate a synthetic image."""
        if not self.is_acquiring:
            return
        if self.random_image:
            image = np.random.normal(
                0,
                self._noise_sigma
                / 0.47,  # TODO: Don't hardcode 0.47 electrons per count
                size=(self.x_pixels, self.y_pixels),
            ).astype(np.uint16) + int(self._mean_background_count)
        else:
            image = self.tif_images[self.current_tif_id][self.img_id]
            self.img_id += 1
            if self.img_id >= len(self.tif_images[self.current_tif_id]):
                self.img_id = 0
                self.current_tif_id = (self.current_tif_id + 1) % len(self.tif_images)

        ctypes.memmove(
            self.data_buffer[self.current_frame_idx].ctypes.data,
            image.ctypes.data,
            self.x_pixels * self.y_pixels * 2,
        )

        self.current_frame_idx = (self.current_frame_idx + 1) % self.num_of_frame

    def get_new_frame(self):
        """Get frame from SyntheticCamera camera."""

        time.sleep(self.camera_exposure_time / 1000)
        timeout = 500
        while self.pre_frame_idx == self.current_frame_idx and timeout:
            time.sleep(0.001)
            timeout -= 1
        if timeout <= 0:
            return []
        if self.pre_frame_idx < self.current_frame_idx:
            frames = list(range(self.pre_frame_idx, self.current_frame_idx))
        else:
            frames = list(range(self.pre_frame_idx, self.num_of_frame))
            frames += list(range(0, self.current_frame_idx))
        self.pre_frame_idx = self.current_frame_idx
        logger.debug(f"Get a new frame from camera, {frames}")
        return frames

    def set_ROI(self, roi_height=2048, roi_width=2048):
        """Change the size of the active region on the camera.

        Parameters
        ----------
        roi_height : int
            Height of active camera region.
        roi_width : int
            Width of active camera region.
        """
        self.x_pixels = roi_width
        self.y_pixels = roi_height

    def get_minimum_waiting_time(self):
        """Get minimum waiting time for SyntheticCamera.

        This function get timing information from the camera device
        cyclic_trigger_period, minimum_trigger_blank, minimum_trigger_interval
        'cyclic_trigger_period' of current device is 0
        according to the document, trigger_blank should be bigger than trigger_interval.
        """
        return 0.01

    def calculate_readout_time(self):
        """Calculate duration of time needed to readout an image. Calculates the readout
        time and maximum frame rate according to the camera configuration settings.

        Returns
        -------
        readout_time : float
            Duration of time needed to readout an image.
        max_frame_rate : float
            Maximum framerate for a given camera acquisition mode.

        """
        exposure_time = self.camera_controller.get_property_value("exposure_time")
        readout_time = 0.01  # 10 milliseconds.
        max_frame_rate = 1 / (exposure_time + readout_time)
        return readout_time, max_frame_rate
