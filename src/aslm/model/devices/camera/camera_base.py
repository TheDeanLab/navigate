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

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class CameraBase:
    r"""CameraBase Parent camera class.

    Parameters
    ----------
    camera_id : int
        Selects which camera to connect to (0, 1, ...).
    configuration : Configurator
        Global configuration of the microscope
    experiment : Configurator
        Experiment configuration of the microscope

    """
    def __init__(self, camera_id, configuration):
        self.configuration = configuration
        self.experiment = self.configuration['experiment']
        self.camera_id = camera_id
        self.stop_flag = False
        self.is_acquiring = False

        # Initialize Pixel Information
        self.pixel_size_in_microns = self.configuration['configuration']['CameraParameters']['pixel_size_in_microns']
        self.binning_string = self.configuration['configuration']['CameraParameters']['binning']
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])
        self.x_pixels = self.configuration['configuration']['CameraParameters']['x_pixels']
        self.y_pixels = self.configuration['configuration']['CameraParameters']['y_pixels']
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        # Initialize Exposure and Display Information - Convert from milliseconds to seconds.
        self.camera_line_interval = self.configuration['configuration']['CameraParameters']['line_interval']
        self.camera_exposure_time = self.configuration['configuration']['CameraParameters']['exposure_time'] / 1000
        self.camera_display_acquisition_subsampling = self.configuration['configuration']['CameraParameters']['display_acquisition_subsampling']

