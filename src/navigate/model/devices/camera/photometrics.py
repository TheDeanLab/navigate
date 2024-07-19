# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below)
# provided that the following conditions are met:

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
from ctypes import *  # noqa
import numpy as np
from pyvcam import pvc
from pyvcam.camera import Camera

# Local Imports
from navigate.model.devices.camera.base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_photometrics_connection(camera_connection):
    """Build Sutter Stage Serial Port connection

    Import Photometrics API and Initialize Camera Controller.

    Parameters
    ----------
    camera_connection : str
        Camera connection string

    Returns
    -------
    camera_to_open : object
        Camera object.
    """
    try:
        pvc.init_pvcam()
        # camera_names = Camera.get_available_camera_names()
        camera_to_open = Camera.select_camera(camera_connection)
        camera_to_open.open()
        return camera_to_open
    except Exception as e:
        logger.debug(f"Could not establish connection with camera: {e}")
        raise UserWarning(
            "Could not establish connection with camera", camera_connection
        )


class PhotometricsBase(CameraBase):
    """Photometrics Base camera class.

    This class is the interface between the rest of the microscope code and the
    Photometrics API. It has been tested with the Photometrics Iris 15


    Note
    ----
        If you want to use a photometrics camera, please go first to the
        PyVCAM-master folder in APIs and run:
        python setup.py install
    """

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize the Photometrics class.

        Parameters
        ---------
        microscope_name : str
                Name of microscope in configuration
        device_connection : object
                Hardware device to connect to. will be saved in camera_controller
        configuration : multiprocesing.managers.DictProxy
                Global configuration of the microscope
        -------

        """
        super().__init__(microscope_name, device_connection, configuration)

        self.camera_parameters["supported_readout_directions"] = [
            "Top-to-Bottom",
            "Bottom-to-Top",
        ]

        #: int: Exposure Time in milliseconds
        self._exposuretime = 20

        #: int: Scan Mode (0 = Normal, 1 = ASLM)
        self._scanmode = 0

        #: int: Scan Delay
        self._scandelay = 1

        #: int: Number of frames
        self._numberofframes = 100

        #: obj: Data Buffer
        self._databuffer = None

        #: int: Number of frames received
        self._frames_received = 0

        #: list: Frame IDs
        self._frame_ids = []

        #: dict: Camera parameters
        self.camera_parameters["x_pixels"] = self.camera_controller.sensor_size[0]
        self.camera_parameters["y_pixels"] = self.camera_controller.sensor_size[1]

        self.set_sensor_mode("Normal")
        self.camera_controller.binning = 1
        # TODO: Implement readout_speed, defect_correct_mode
        self.camera_controller.exp_mode = "Edge Trigger"
        self.camera_controller.prog_scan_dir = 0

        # Photometrics camera settings from config file
        self.camera_controller.readout_port = self.camera_parameters["readout_port"]
        self.camera_controller.speed_table_index = self.camera_parameters[
            "speed_table_index"
        ]
        self.camera_controller.gain = self.camera_parameters["gain"]

        logger.info("Photometrics Initialized")

    def __del__(self):
        """Delete PhotometricsBase object."""
        if hasattr(self, "camera_controller"):
            self.camera_controller.close()
        logger.info("PhotometricsBase Shutdown")

    @property
    def serial_number(self):
        """Get Camera Serial Number

        Returns
        -------
        serial_number : str
            Serial number for the camera.
        """
        return self.camera_controller.serial_no

    def report_settings(self):
        """Print Camera Settings."""
        # TODO: complete param recording
        print("sensor_mode: " + str(self.camera_controller.prog_scan_mode))
        print("binning: " + str(self.camera_controller.binning))
        print("readout_speed" + str(self.camera_controller.readout_time))
        print("trigger_active")
        print("trigger_mode")
        print("trigger_polarity")
        print("trigger_source")
        print("internal_line_interval")
        print("sensor size" + str(self.camera_controller.sensor_size))
        print("image_height and width" + str(self.x_pixels) + ", " + str(self.y_pixels))
        print("exposure_time" + str(self._exposuretime))

    def close_camera(self):
        """Close Photometrics Camera"""
        self.camera_controller.close()

    def set_sensor_mode(self, mode):
        """Set Photometrics sensor mode

        Can be normal or programmable scan mode (e.g., ASLM).

        Parameters
        ----------
        mode : str
            'Normal' (static) or 'Light-Sheet' (ASLM)
        """
        modes_dict = {"Normal": 0, "Light-Sheet": 1}
        if mode in modes_dict:
            self.camera_controller.prog_scan_mode = modes_dict[mode]
            self._scanmode = modes_dict[mode]
        else:
            print("Camera mode not supported" + str(modes_dict[mode]))
            logger.info("Camera mode not supported" + str(modes_dict[mode]))

    def set_readout_direction(self, mode):
        """Set Photometrics readout direction.

        Parameters
        ----------
        mode : str
            'Top-to-Bottom', 'Bottom-to-Top', 'Alternate'
            Scan direction options: {'Down': 0, 'Up': 1, 'Down/Up Alternate': 2}

        """
        # print("available scan directions on camera are:")
        # print(str(self.camera_controller.prog_scan_dirs))

        if mode == "Top-to-Bottom":
            #  'Down' readout direction
            self.camera_controller.prog_scan_dir = 0
        elif mode == "Bottom-to-Top":
            #  'Up' readout direction
            self.camera_controller.prog_scan_dir = 1
        elif mode == "Alternate":
            self.camera_controller.prog_scan_dir = 2
        else:
            logger.info("Camera readout direction not supported")

    def calculate_readout_time(self):
        """Calculate duration of time needed to readout an image.

        Calculates the readout time and maximum frame rate according to the camera
        configuration settings.

        Note
        ----
            Function only called for normal acquisition mode.

        Returns
        -------
        readout_time : float
            Duration of time needed to readout an image in seconds.
        """

        # get the readout time from the Photometrics camera in us
        readout_time_ms = self.camera_controller.readout_time / 1000

        return readout_time_ms / 1000

    def set_exposure_time(self, exposure_time):
        """Set Photometrics exposure time.

        Note: Units of the Photometrics API are in milliseconds

        Parameters
        ----------
        exposure_time : float
            Exposure time in seconds.

        Returns
        -------
        exposure_time : float
            Exposure time in milliseconds.
        """
        self._exposuretime = int(exposure_time * 1000)
        self.camera_controller.exp_time = self._exposuretime
        self.camera_controller.start_live(self._exposuretime)
        return exposure_time

    def set_line_interval(self, line_interval_time):
        """Set Photometrics line interval.

        Parameters
        ----------
        line_interval_time : float
            Line interval duration.
        """
        # todo calculate line delay from scandelay
        self._scandelay = line_interval_time
        self.camera_controller.prog_scan_line_delay = line_interval_time

    def calculate_light_sheet_exposure_time(
        self, full_chip_exposure_time, shutter_width
    ):
        """Convert normal mode exposure time to light-sheet mode exposure time.
        Calculate the parameters for an ASLM acquisition

        Parameters
        ----------
        full_chip_exposure_time : float
            Normal mode exposure time in seconds
        shutter_width : int
            Shutter width in pixels

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time in seconds
        camera_line_interval : float
            HamamatsuOrca line interval duration.
        full_chip_exposure_time : float
            Full chip exposure time (s)
        """

        # size of ROI
        nbrows = self.y_pixels

        # transform exposure time to milliseconds for Photometrics API.
        full_chip_exposure_time = full_chip_exposure_time * 1000

        # equations to calculate ASLM parameters
        linedelay = self.camera_parameters["unitforlinedelay"] / 1000
        ASLM_lineExposure = int(
            np.ceil(full_chip_exposure_time / (1 + (1 + nbrows) / shutter_width))
        )
        ASLM_line_delay = (
            int(
                np.ceil(
                    (full_chip_exposure_time - ASLM_lineExposure)
                    / ((nbrows + 1) * linedelay)
                )
            )
            - 1
        )

        ASLM_acquisition_time = (
            (ASLM_line_delay + 1) * nbrows * linedelay
            + ASLM_lineExposure
            + (ASLM_line_delay + 1) * linedelay
        )

        self.camera_parameters["line_interval"] = ASLM_lineExposure
        self._exposuretime = ASLM_lineExposure
        self._scandelay = ASLM_line_delay
        return ASLM_lineExposure / 1000, ASLM_line_delay, ASLM_acquisition_time / 1000

    def set_binning(self, binning_string):
        """Set Photometrics binning mode.

        Parameters
        ----------
        binning_string : str
            Desired binning properties (e.g., '1x1', '2x2',
            '4x4', '8x8', '16x16', '1x2', '2x4')

        Returns
        -------
        result: bool
            True if binning was set successfully, False otherwise.

        """
        binning_dict = {
            "1x1": 1,
            "2x2": 2,
            "4x4": 4,
            "8x8": 8,
        }
        if binning_string not in binning_dict.keys():
            logger.debug(f"can't set binning to {binning_string}")
            print(f"Can't set binning to {binning_string}")
            return False
        self.camera_controller.binning = binning_dict[binning_string]
        idx = binning_string.index("x")

        #: int: Binning in x direction
        self.x_binning = int(binning_string[:idx])

        #: int: Binning in y direction
        self.y_binning = int(binning_string[idx + 1 :])

        #: int: Number of pixels in x direction
        self.x_pixels = int(self.x_pixels / self.x_binning)

        #: int: Number of pixels in y direction
        self.y_pixels = int(self.y_pixels / self.y_binning)
        return True

    def set_ROI(self, roi_height=3200, roi_width=3200):
        """Change the size of the active region on the camera.

        Parameters
        ----------
        roi_height : int
            Height of active camera region. Default is 3200.
        roi_width : int
            Width of active camera region. Default is 3200.

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
            or roi_height % 2 == 1
            or roi_width % 2 == 1
        ):
            logger.debug(f"can't set roi to {roi_width} and {roi_height}")
            return False

        # Calculate Location of Image Edges
        roi_top = (camera_height - roi_height) / 2
        roi_bottom = roi_top + roi_height - 1
        roi_left = (camera_width - roi_width) / 2

        if roi_top % 2 != 0 or roi_bottom % 2 == 0:
            logger.debug(f"can't set ROI to {roi_width} and {roi_height}")
            return False

        # Set ROI
        self.camera_controller.set_roi(roi_left, roi_top, roi_width, roi_height)
        logger.info(f"Photometrics ROI shape, {self.camera_controller.shape()}")
        return self.x_pixels == roi_width and self.y_pixels == roi_height

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        """Initialize Photometrics image series. This is for starting stacks etc.

        Parameters
        ----------
        data_buffer :
            List of SharedNDArrays of shape=(self.img_height,
            self.img_width) and dtype="uint16"
            Default is None.
        number_of_frames : int
            Number of frames.  Default is 100.
        """

        # set camera parameters depending on acquisition mode
        self._scanmode = self.camera_controller.prog_scan_mode
        if self._scanmode == 1:
            # Programmable scan mode (ASLM)
            self.camera_controller.exp_mode = "Edge Trigger"
            self.camera_controller.prog_scan_line_delay = self._scandelay
            self.camera_controller.exp_out_mode = 4
            print(
                "camera ready to acquire programmable scan mode "
                "with scandelay {}".format(self._scandelay)
            )
        else:
            # Normal mode
            self.camera_controller.exp_out_mode = "Any Row"
            self.camera_controller.exp_mode = "Edge Trigger"
            print("camera ready to acquire static light sheet mode")

        # Prepare for buffered acquisition
        #: int: Number of frames
        self._numberofframes = number_of_frames

        #: obj: Data Buffer
        self._data_buffer = data_buffer

        #: int: Number of frames received
        self._frames_received = 0

        #: list: Frame IDs
        self._frame_ids = []

        #: bool: Acquisition flag
        self.is_acquiring = True

        # Start camera - call it here as there are some error messages showing up
        # a call to the camera here.
        # Start live will be called a second time from the exposure time function,
        # with the current exposure time.
        self.camera_controller.start_live()

    def _receive_images(self):
        """
        Update image in the data buffer if the Photometrics camera acquired a new
        image and return frame ids.

        Returns
        -------
        frame : numpy.ndarray
            Frame ids from Photometrics camera that point to newly acquired data in
            data buffer
        """
        # Try to grap the next frame from camera
        try:
            frame, fps, frame_count = self.camera_controller.poll_frame(
                timeout_ms=10000
            )
            self._data_buffer[self._frames_received][:, :] = np.copy(
                frame["pixel_data"][:]
            )
            # Delete copied frame for memory management
            frame = None
            del frame
            self._frames_received += 1
            if self._frames_received >= self._numberofframes:
                self._frames_received = 1
            return [self._frames_received - 1]
        except Exception as e:
            print(str(e))

        return []

    def get_new_frame(self):
        """
        Call update function for data buffer and get frame ids from Photometrics camera.

        Returns
        -------
        frame : numpy.ndarray
            Frame ids from Photometrics camera that point to newly acquired
            data in data buffer
        """
        return self._receive_images()

    def close_image_series(self):
        """Close Photometrics image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        self.camera_controller.finish()
        self.is_acquiring = False
