# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
# you shouldn't need to call this as self.controller is the camera object
# and should have everything needed
from ctypes import *  # noqa
import numpy as np

# Local Imports
from navigate.model.devices.camera.camera_base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class PhotometricsKinetix(CameraBase):
    """Photometrics Kinetix camera class.

    This class is the interface between the rest of the microscope code and the
    Photometrics API.
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
        #: float: Unit for line delay
        self._unitforlinedelay = 0.00375  # 3.75  us for dynamic mode kinetix
        #: list: Frame IDs
        self._frame_ids = []
        #: dict: Camera parameters
        self.camera_parameters["x_pixels"] = self.camera_controller.sensor_size[0]
        self.camera_parameters["y_pixels"] = self.camera_controller.sensor_size[1]

        # todo: complete first init of parameters to default values

        # Values are pulled from the CameraParameters section of the
        # configuration.yml file.
        # Exposure time converted here from milliseconds to seconds.
        self.set_sensor_mode("Normal")
        self.camera_controller.binning = 1
        # not implemented: readout_speed, defect_correct_mode
        self.camera_controller.exp_mode = "Edge Trigger"
        self.camera_controller.prog_scan_dir = 0
        # self.camera_controller.speed_table_index = 1 # 1 for 100 MHz
        self.camera_controller.readout_port = 0
        self.camera_controller.gain = 1
        #
        # self.camera_controller.set_property_value("trigger_active",
        #                                           self.camera_parameters[
        #                                           'trigger_active'])
        # self.camera_controller.set_property_value("trigger_mode",
        #                                           self.camera_parameters[
        #                                           'trigger_mode'])
        # self.camera_controller.set_property_value("trigger_polarity",
        #                                           self.camera_parameters[
        #                                           \'trigger_polarity'])
        # self.camera_controller.set_property_value("trigger_source",
        #                                           self.camera_parameters[
        #                                           'trigger_source'])
        # # DCAM_IDPROP_IMAGE_WIDTH/HEIGHT is readonly
        # self.camera_controller.set_property_value("image_height",
        #                                            self.camera_parameters[
        #                                            'y_pixels'])
        # self.camera_controller.set_property_value("image_width",
        #                                            self.camera_parameters[
        #                                            'x_pixels'])

        logger.info("Photometrics Initialized")

    def __del__(self):
        """Delete PhotometricsKinetix object."""
        if hasattr(self, "camera_controller"):
            self.camera_controller.close()
            # pvc.uninit_pvcam()
            print("camera closed")
        logger.info("PhotometricsKinetix Shutdown")

    @property
    def serial_number(self):
        """Get Camera Serial Number

        Returns
        -------
        serial_number : str
            Serial number for the camera.
        """
        # return self.camera_controller._serial_number
        ser_no = self.camera_controller.serial_no
        return ser_no

    def report_settings(self):
        """Print Camera Settings."""
        # todo: complete param recording
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
        """Close Photometrics Kinetix Camera"""
        self.camera_controller.close()

    def set_sensor_mode(self, mode):
        """Set Photometrics sensor mode

        Can be normal or programmable scan mode (e.g., ASLM).

        Parameters
        ----------
        mode : str
            'Normal (static)' or 'Light-Sheet (ASLM)'
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
        print("available scan directions on camera are:")
        print(str(self.camera_controller.prog_scan_dirs))

        if mode == "Top-to-Bottom":
            #  'Down' readout direction
            self.camera_controller.prog_scan_dir = 0
        elif mode == "Bottom-to-Top":
            #  'Up' readout direction
            self.camera_controller.prog_scan_dir = 1
        elif mode == "Alternate":
            self.camera_controller.prog_scan_dir = 2
        else:
            print("Camera readout direction not supported")
            logger.info("Camera readout direction not supported")

    def calculate_readout_time(self):
        """Calculate duration of time needed to readout an image.

        Calculates the readout time and maximum frame rate according to the camera
        configuration settings.

        Warn
        ----
            Not implemented. Currently hard-coded for Hamamatsu Orca Flash 4.0.

        Returns
        -------
        readout_time : float
            Duration of time needed to readout an image.
        """

        # todo
        h = 3.75 * 10**-6  # Readout timing constant
        # h = self.camera_controller.get_property_value("readout_time")
        vn = self.y_pixels
        exposure_time = self._exposuretime
        # trigger_source = self.camera_controller.get_property_value('trigger_source')
        # trigger_active = self.camera_controller.get_property_value('trigger_active')
        #
        if self._scanmode == 0:  # normal/static light-sheet
            readout_time = exposure_time - ((vn + 10) * h + exposure_time)
        else:
            # todo: not sure if these equations are correct
            readout_time = exposure_time - (
                (vn + 10) * h * self._scandelay + exposure_time
            )

            #
        #     #  Area sensor mode operation
        #     if trigger_source == 1:
        #         # Internal Trigger Source
        #         max_frame_rate = 1 / ((vn / 2) * h)
        #         readout_time = exposure_time - ((vn / 2) * h)
        #
        #     if trigger_active == 1 or 2:
        #         #  External Trigger Source
        #         #  Edge == 1, Level == 2
        #         max_frame_rate = 1 / ((vn / 2) * h + exposure_time + 10 * h)
        #         readout_time = exposure_time - ((vn / 2) * h + exposure_time + 10 * h)
        #
        #     if trigger_active == 3:
        #         #  External Trigger Source
        #         #  Synchronous Readout == 3
        #         max_frame_rate = 1 / ((vn / 2) * h + 5 * h)
        #         readout_time = exposure_time - ((vn / 2) * h + 5 * h)
        #
        # if sensor_mode == 12:
        #     #  Progressive sensor mode operation
        #     max_frame_rate = 1 / (exposure_time + (vn + 10) * h)
        #     readout_time = exposure_time - 1 / (exposure_time + (vn + 10) * h)
        #
        return readout_time

    def set_exposure_time(self, exposure_time):
        """Set Photometrics exposure time.

        Units of the Photometrics API are in seconds.
        All of our units are in milliseconds.

        Parameters
        ----------
        exposure_time : float
            Exposure time in milliseconds.

        Returns
        -------
        exposure_time : float
            Exposure time in seconds.
        """
        self._exposuretime = exposure_time
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

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time.
        camera_line_interval : float
            HamamatsuOrca line interval duration.
        """
        linedelay = self._unitforlinedelay  # 10.16us
        nbrows = self.y_pixels
        ASLM_scanWidth = 70

        ASLM_lineExposure = int(
            np.ceil(full_chip_exposure_time / (1 + nbrows / ASLM_scanWidth))
        )
        ASLM_line_delay = (
            int(
                np.ceil(
                    (full_chip_exposure_time - ASLM_lineExposure) / (nbrows * linedelay)
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
        print(
            "ASLM parameters are: {} exposure time, and {} line delay factor, {} "
            "total acquisition time for {} scan width".format(
                ASLM_lineExposure,
                ASLM_line_delay,
                ASLM_acquisition_time,
                ASLM_scanWidth,
            )
        )

        return ASLM_lineExposure, ASLM_line_delay

    def _calculate_ASLMparameters(self, desired_exposuretime):
        """Calculate the parameters for an ASLM acquisition

        Parameters
        ----------
        desired_exposuretime : float
            Exposure time in milliseconds.

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time.

        Warn
        ----
            Not implemented. No code in this function.
        """

    def set_binning(self, binning_string):
        """Set HamamatsuOrca binning mode.

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
        }
        if binning_string not in binning_dict.keys():
            logger.debug(f"can't set binning to {binning_string}")
            print(f"can't set binning to {binning_string}")
            return False
        self.camera_controller.binning = binning_dict[binning_string]
        idx = binning_string.index("x")
        #: int: Binning in x direction
        self.x_binning = int(binning_string[:idx])
        #: int: Binning in y direction
        self.y_binning = int(binning_string[idx + 1 :])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        # should update experiment in controller side
        # self.configuration['experiment']['CameraParameters']['camera_binning'] = str(
        # self.x_binning) + 'x' + str(self.y_binning)
        return True

    def set_ROI(self, roi_height=3200, roi_width=3200):
        """Change the size of the active region on the camera.

        Parameters
        ----------
        roi_height : int
            Height of active camera region.
        roi_width : int
            Width of active camera region.
        """
        # Get the Maximum Number of Pixels from the Configuration File
        camera_height = self.camera_parameters["y_pixels"]
        camera_width = self.camera_parameters["x_pixels"]

        if (
            roi_height > camera_height
            or roi_width > camera_width
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
        # self.x_pixels, self.y_pixels = self.camera_controller.shape()

        logger.info(f"Photometrics ROI shape, {self.camera_controller.shape()}")

        return self.x_pixels == roi_width and self.y_pixels == roi_height

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        """Initialize Photometrics image series. This is for starting stacks etc.

        Parameters
        ----------
        data_buffer : int
            Size of the data to buffer.  Default is None.
        number_of_frames : int
            Number of frames.  Default is 100.
        """
        print(self._exposuretime)
        self.camera_controller.readout_port = 0
        self.camera_controller.speed_table_index = 0
        self.camera_controller.gain = 1
        self._exposuretime = 20

        # set following parameters if in programmable scan mode (ASLM)
        self._scanmode = self.camera_controller.prog_scan_mode
        if self._scanmode == 1:
            self.camera_controller.exp_mode = "Edge Trigger"
            self.camera_controller.prog_scan_line_delay = self._scandelay
            self.camera_controller.exp_out_mode = 4
            print("camera ready to acquire programmable scan mode")

        else:
            self.camera_controller.exp_out_mode = "Any Row"
            self.camera_controller.exp_mode = "Edge Trigger"
            print("camera ready to acquire static light sheet mode")

        # prepare buffer pointer array
        # ptr_array = c_void_p * number_of_frames
        # data_ptr = ptr_array()
        # for i in range(number_of_frames):
        #     np_array = data_buffer[i]
        #     data_ptr[i] = np_array.ctypes.data

        self._numberofframes = number_of_frames
        self._data_buffer = data_buffer
        self._frames_received = 0
        self._frame_ids = []

        self.is_acquiring = True
        self.camera_controller.start_live(exp_time=self._exposuretime)

    def _receive_images(self):

        # wait_for_camera = True

        # while self.is_acquiring == True:

        # time.sleep(0.002)
        try:
            frame, fps, frame_count = self.camera_controller.poll_frame(
                timeout_ms=10000
            )
            # self._frame_ids.append(self._frames_received)

            self._data_buffer[self._frames_received][:, :] = np.copy(
                frame["pixel_data"][:]
            )
            frame = None
            del frame
            self._frames_received += 1
            if self._frames_received >= self._numberofframes:
                self._frames_received = 0
            return [self._frames_received - 1]
        except Exception as e:
            print(str(e))
        #     break

        # print("excited loop")

        return []

    # def _receive_imagesV1(self):
    #
    #     frame_ids = []
    #     wait_for_camera=True
    #     print("wait to receive frames")
    #
    #
    #     while wait_for_camera ==True:
    #         time.sleep(0.002)
    #         print(self.camera_controller.check_frame_status())
    #         if self.camera_controller.check_frame_status()=='FRAME_AVAILABLE':
    #             # framesReceived < number_of_frames:
    #
    #             if self.is_acquiring==False: #exit if acquisition is done
    #                 break
    #
    #             print(self._frames_received)
    #             try:
    #                 frame, fps, frame_count = self.camera_controller.poll_frame(
    #                 timeout_ms=10000)
    #                 print("received frame")
    #                 frame_ids.append(self._frames_received)
    #                 self.data_buffer[self._frames_received][:,:] = np.copy(frame[
    #                 'pixel_data'][:])
    #                 frame = None
    #                 del frame
    #                 self._frames_received += 1
    #                 if self._frames_received >= self._numberofframes:
    #                     self._frames_received = 0
    #
    #
    #
    #
    #             except Exception as e:
    #                 print(str(e))
    #                 break
    #     return frame_ids

    def close_image_series(self):
        """Close image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        print("Calling finish")
        self.camera_controller.finish()
        self.is_acquiring = False

    def get_new_frame(self):
        """Get frame ids from Photometrics camera."""
        # return self.camera_controller.get_frame(exp_time=self._exposuretime)
        # self.camera_controller.start_live(exp_time=self._exposuretime)

        # self._receive_images()
        # return self._frame_ids[]

        return self._receive_images()

    def get_minimum_waiting_time(self):
        """Get minimum waiting time for HamamatsuOrca.

        This function get timing information from the camera device
        cyclic_trigger_period, minimum_trigger_blank, minimum_trigger_interval
        'cyclic_trigger_period' of current device is 0
        according to the document, trigger_blank should be bigger than trigger_interval.
        """
        # # cyclic_trigger = self.camera_controller.get_property_value(
        # 'cyclic_trigger_period')
        # trigger_blank = self.camera_controller.get_property_value(
        # 'minimum_trigger_blank')
        # # trigger_interval = self.camera_controller.get_property_value(
        # 'minimum_trigger_interval')
        # return trigger_blank
        # readout_time = (self.y_pixels + 1) * Camera_parameters.highres_
        # line_digitization_time  # +1 for the reset time at the first row
        # before the start
        # minimal_trigger_timeinterval = self._exposuretime + readout_time
        return 2
