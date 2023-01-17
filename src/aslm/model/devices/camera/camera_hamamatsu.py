# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

# Local Imports
from aslm.model.devices.camera.camera_base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class HamamatsuOrca(CameraBase):
    r"""HamamatsuOrca camera class.

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

        # Values are pulled from the CameraParameters section of the configuration.yml file.
        # Exposure time converted here from milliseconds to seconds.
        self.set_sensor_mode(self.camera_parameters["sensor_mode"])

        self.camera_controller.set_property_value(
            "defect_correct_mode", self.camera_parameters["defect_correct_mode"]
        )
        self.camera_controller.set_property_value(
            "exposure_time", self.camera_parameters["exposure_time"] / 1000
        )
        self.camera_controller.set_property_value(
            "binning", int(self.camera_parameters["binning"][0])
        )
        self.camera_controller.set_property_value(
            "readout_speed", self.camera_parameters["readout_speed"]
        )
        self.camera_controller.set_property_value(
            "trigger_active", self.camera_parameters["trigger_active"]
        )
        self.camera_controller.set_property_value(
            "trigger_mode", self.camera_parameters["trigger_mode"]
        )
        self.camera_controller.set_property_value(
            "trigger_polarity", self.camera_parameters["trigger_polarity"]
        )
        self.camera_controller.set_property_value(
            "trigger_source", self.camera_parameters["trigger_source"]
        )
        # DCAM_IDPROP_IMAGE_WIDTH/HEIGHT is readonly
        # self.camera_controller.set_property_value("image_height",
        #                                            self.camera_parameters['y_pixels'])
        # self.camera_controller.set_property_value("image_width",
        #                                            self.camera_parameters['x_pixels'])

        logger.info("HamamatsuOrca Initialized")

    def __del__(self):
        """Delete Hamamatsu Camera Controller Object"""
        if hasattr(self, 'camera_controller'):
            self.camera_controller.dev_close()
        logger.info("HamamatsuOrca Shutdown")

    @property
    def serial_number(self):
        r"""Get Camera Serial Number

        Returns
        -------
        serial_number : str
            Serial number for the camera.
        """
        return self.camera_controller._serial_number

    def report_settings(self):
        r"""Print Camera Settings."""
        params = [
            "defect_correct_mode",
            "sensor_mode",
            "binning",
            "readout_speed",
            "trigger_active",
            "trigger_mode",
            "trigger_polarity",
            "trigger_source",
            "internal_line_interval",
            "image_height",
            "image_width",
            "exposure_time",
        ]
        for param in params:
            print(param, self.camera_controller.get_property_value(param))
            logger.info(param, self.camera_controller.get_property_value(param))

    def close_camera(self):
        r"""Close HamamatsuOrca Camera"""
        self.camera_controller.dev_close()

    def set_sensor_mode(self, mode):
        r"""Set HamamatsuOrca sensor mode.

        Parameters
        ----------
        mode : str
            'Normal' or 'Light-Sheet'
        """
        modes_dict = {"Normal": 1, "Light-Sheet": 12}
        if mode in modes_dict:
            self.camera_controller.set_property_value("sensor_mode", modes_dict[mode])
        else:
            print("Camera mode not supported")
            logger.info("Camera mode not supported")

        # print("Camera Sensor Mode:", self.camera_controller.get_property_value("sensor_mode"))

    def set_readout_direction(self, mode):
        r"""Set HamamatsuOrca readout direction.

        Parameters
        ----------
            mode : str
                'Top-to-Bottom', 'Bottom-to-Top', 'bytrigger', or 'diverge'.
        """
        if mode == "Top-to-Bottom":
            #  'Forward' readout direction
            self.camera_controller.set_property_value("readout_direction", 1.0)
        elif mode == "Bottom-to-Top":
            #  'Backward' readout direction
            self.camera_controller.set_property_value("readout_direction", 2.0)
        elif mode == "bytrigger":
            self.camera_controller.set_property_value("readout_direction", 3.0)
        elif mode == "diverge":
            self.camera_controller.set_property_value("readout_direction", 5.0)
        else:
            print("Camera readout direction not supported")
            logger.info("Camera readout direction not supported")

    def calculate_readout_time(self):
        r"""Calculate duration of time needed to readout an image.
        Calculates the readout time and maximum frame rate according to the camera configuration settings.
        Assumes model C13440 with Camera Link communication from Hamamatsu.
        Currently pulling values directly from the camera.

        Returns
        -------
        readout_time : float
            Duration of time needed to readout an image.
        max_frame_rate : float
            Maximum framerate for a given camera acquisition mode.

        TODO: I think self.camera_controller.get_property_value("readout_time") pulls out the actual readout_time
              calculated here (i.e. we don't need to do the calculations).
        """
        h = 9.74436 * 10**-6  # Readout timing constant
        h = self.camera_controller.get_property_value("readout_time")
        vn = self.camera_controller.get_property_value("subarray_vsize")
        sensor_mode = self.camera_controller.get_property_value("sensor_mode")
        exposure_time = self.camera_controller.get_property_value("exposure_time")
        trigger_source = self.camera_controller.get_property_value("trigger_source")
        trigger_active = self.camera_controller.get_property_value("trigger_active")

        if sensor_mode == 1:
            #  Area sensor mode operation
            if trigger_source == 1:
                # Internal Trigger Source
                max_frame_rate = 1 / ((vn / 2) * h)
                readout_time = exposure_time - ((vn / 2) * h)

            if trigger_active == 1 or 2:
                #  External Trigger Source
                #  Edge == 1, Level == 2
                max_frame_rate = 1 / ((vn / 2) * h + exposure_time + 10 * h)
                readout_time = exposure_time - ((vn / 2) * h + exposure_time + 10 * h)

            if trigger_active == 3:
                #  External Trigger Source
                #  Synchronous Readout == 3
                max_frame_rate = 1 / ((vn / 2) * h + 5 * h)
                readout_time = exposure_time - ((vn / 2) * h + 5 * h)

        if sensor_mode == 12:
            #  Progressive sensor mode operation
            max_frame_rate = 1 / (exposure_time + (vn + 10) * h)
            readout_time = exposure_time - 1 / (exposure_time + (vn + 10) * h)

        return readout_time, max_frame_rate

    def set_exposure_time(self, exposure_time):
        r"""Set HamamatsuOrca exposure time.

        Units of the Hamamatsu API are in seconds.
        All of our units are in milliseconds. Function convert to seconds.

        Parameters
        ----------
        exposure_time : float
            Exposure time in milliseconds.

        """
        exposure_time = exposure_time / 1000
        return self.camera_controller.set_property_value("exposure_time", exposure_time)

    def set_line_interval(self, line_interval_time):
        r"""Set HamamatsuOrca line interval.

        Parameters
        ----------
        line_interval_time : float
            Line interval duration.
        """
        return self.camera_controller.set_property_value(
            "internal_line_interval", line_interval_time
        )

    def set_binning(self, binning_string):
        r"""Set HamamatsuOrca binning mode.

        Parameters
        ----------
        binning_string : str
            Desired binning properties (e.g., '1x1', '2x2', '4x4', '8x8', '16x16', '1x2', '2x4')

        Returns
        -------
        result: bool
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
        idx = binning_string.index("x")
        self.x_binning = int(binning_string[:idx])
        self.y_binning = int(binning_string[idx + 1 :])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        # should update experiment in controller side
        # self.configuration['experiment']['CameraParameters']['camera_binning'] = str(self.x_binning) + 'x' + str(self.y_binning)
        return True

    def set_ROI(self, roi_height=2048, roi_width=2048):
        r"""Change the size of the active region on the camera.

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
        roi_right = roi_left + roi_width - 1

        if roi_top % 2 != 0 or roi_bottom % 2 == 0:
            logger.debug(f"can't set ROI to {roi_width} and {roi_height}")
            return False

        # Set ROI
        self.x_pixels, self.y_pixels = self.camera_controller.set_ROI(
            roi_left, roi_top, roi_right, roi_bottom
        )

        logger.info(
            f"HamamatsuOrca - subarray_hpos, {self.camera_controller.get_property_value('subarray_hpos')}"
        )
        logger.info(
            f"HamamatsuOrca - subarray_hsize,{self.camera_controller.get_property_value('subarray_hsize')}"
        )
        logger.info(
            f"HamamatsuOrca - subarray_vpos, {self.camera_controller.get_property_value('subarray_vpos')}"
        )
        logger.info(
            f"HamamatsuOrca - subarray_vsize,{self.camera_controller.get_property_value('subarray_vsize')}"
        )

        return self.x_pixels == roi_width and self.y_pixels == roi_height

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        r"""Initialize HamamatsuOrca image series.

        Parameters
        ----------
        data_buffer : int
            Size of the data to buffer.  Default is None.
        number_of_frames : int
            Number of frames.  Default is 100.
        """
        self.camera_controller.start_acquisition(data_buffer, number_of_frames)
        self.is_acquiring = True

    def close_image_series(self):
        r"""Close image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        self.camera_controller.stop_acquisition()
        self.is_acquiring = False

    def get_new_frame(self):
        r"""Get frame from HamamatsuOrca camera."""
        return self.camera_controller.get_frames()

    def get_minimum_waiting_time(self):
        r"""Get minimum waiting time for HamamatsuOrca.

        This function get timing information from the camera device
        cyclic_trigger_period, minimum_trigger_blank, minimum_trigger_interval
        'cyclic_trigger_period' of current device is 0
        according to the document, trigger_blank should be bigger than trigger_interval.
        """
        # cyclic_trigger = self.camera_controller.get_property_value('cyclic_trigger_period')
        trigger_blank = self.camera_controller.get_property_value(
            "minimum_trigger_blank"
        )
        # trigger_interval = self.camera_controller.get_property_value('minimum_trigger_interval')
        return trigger_blank
