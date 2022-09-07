"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard Library Imports
import logging
import time
import ctypes

# Third Party Imports
import numpy as np
from tifffile import TiffFile

# Local Imports
from aslm.model.analysis import noise_model
from aslm.model.devices.camera.camera_base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class SyntheticCameraController:
    r"""SyntheticCameraController. Synthetic Camera API."""
    def __init__(self):
        self.is_acquiring = False

    def get_property_value(self, name):
        r"""Provides the idprop value after looking it up in the property_dict

        Parameters
        name : str
            Not currently used.

        Returns
        -------
        property_value : int
            Currently hard-coded to -1.
        """
        # return self.prop_getvalue(property_dict[name])

        return -1  # {}


class SyntheticCamera(CameraBase):
    r"""SyntheticCamera camera class.

    Parameters
    ----------
    camera_id : int
        Selects which camera to connect to (0, 1, ...).
    configuration : Configurator
        Global configuration of the microscope
    experiment : Configurator
        Experiment configuration of the microscope

    """
    def __init__(self, camera_id, configuration, experiment):
        super().__init__(camera_id, configuration, experiment)

        self.x_pixels = experiment.CameraParameters['x_pixels']
        self.y_pixels = experiment.CameraParameters['y_pixels']
        self.is_acquiring = False
        self._mean_background_count = 100.0
        self._noise_sigma = noise_model.compute_noise_sigma(Ib=self._mean_background_count)
        self.blah = noise_model.compute_noise_sigma
        self.camera_controller = SyntheticCameraController()
        self.current_frame_idx = None
        self.data_buffer = None
        self.num_of_frame = None
        self.pre_frame_idx = None
        self.random_image = True

        if camera_id == 0:
            self.serial_number = configuration.CameraParameters['low_serial_number']
        else:
            self.serial_number = configuration.CameraParameters['high_serial_number']

        logger.info("SyntheticCamera Class Initialized")

    def __del__(self):
        logger.info("SyntheticCamera Shutdown")
        pass

    def stop(self):
        r""" Set stop_flag as True"""
        self.stop_flag = True

    def report_settings(self):
        r"""Print Camera Settings."""
        pass

    def close_camera(self):
        r"""Close SyntheticCamera Camera"""
        pass

    def set_sensor_mode(self, mode):
        r"""Set SyntheticCamera sensor mode.

        Parameters
        ----------
        mode : str
            'Normal' or 'Light-Sheet'
        """
        pass

    def set_exposure_time(self, exposure_time):
        r"""Set SyntheticCamera exposure time.

        All of our units are in milliseconds. Function convert to seconds.

        Parameters
        ----------
        exposure_time : float
            Exposure time in milliseconds.

        """
        self.camera_exposure_time = exposure_time / 1000

    def set_line_interval(self, line_interval_time):
        r"""Set SyntheticCamera line interval.

        Parameters
        ----------
        line_interval_time : float
            Line interval duration.
        """
        pass

    def set_binning(self, binning_string):
        r"""Set SyntheticCamera binning mode.

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
        r"""Initialize SyntheticCamera image series.

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
        self.camera_controller.is_acquiring = True

    def close_image_series(self):
        r"""Close image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        self.pre_frame_idx = 0
        self.current_frame_idx = 0
        self.camera_controller.is_acquiring = False

    def load_images(self, filenames=None):
        if filenames is None:
            self.random_image = True
        else:
            self.random_image = False
            self.img_id = 0
            self.img_max_id = self.num_of_frame
            idx = 0
            for image_file in filenames:
                try:
                    tif_images = TiffFile(image_file)
                    for img_id in range(len(tif_images.pages)):
                        image = tif_images.pages[img_id].asarray()
                        ctypes.memmove(self.data_buffer[idx].ctypes.data,
                                        image.ctypes.data, self.x_pixels * self.y_pixels * 2)
                        idx += 1
                        if idx >= self.num_of_frame:
                            return
                except:
                    pass
            self.img_max_id = idx
            if self.img_max_id == 0:
                self.random_image = False


    def generate_new_frame(self):
        r"""Generate a synthetic image."""
        if self.random_image:
            image = np.random.normal(self._mean_background_count,
                                    self._noise_sigma,
                                    size=(self.x_pixels, self.y_pixels),
                                    ).astype(np.uint16)
            
            ctypes.memmove(self.data_buffer[self.current_frame_idx].ctypes.data,
                        image.ctypes.data, self.x_pixels * self.y_pixels * 2)

            self.current_frame_idx = (self.current_frame_idx + 1) % self.num_of_frame
        else:
            self.img_id = (self.img_id + 1) % self.img_max_id
            self.current_frame_idx = self.img_id

    def get_new_frame(self):
        r"""Get frame from SyntheticCamera camera."""

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
        r"""Change the size of the active region on the camera.

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
        r"""Get minimum waiting time for SyntheticCamera.

        This function get timing information from the camera device
        cyclic_trigger_period, minimum_trigger_blank, minimum_trigger_interval
        'cyclic_trigger_period' of current device is 0
        according to the document, trigger_blank should be bigger than trigger_interval.
        """
        return 0.01


