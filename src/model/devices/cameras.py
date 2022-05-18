"""
ASLM camera communication classes.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
import time
import ctypes
import importlib

# Third Party Imports
import numpy as np

# Local Imports



class CameraBase:
    def __init__(self, camera_id, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.camera_id = camera_id
        self.verbose = verbose
        self.stop_flag = False

        # Initialize Pixel Information
        self.pixel_size_in_microns = self.model.CameraParameters['pixel_size_in_microns']
        self.binning_string = self.model.CameraParameters['binning']
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])
        self.x_pixels = self.model.CameraParameters['x_pixels']
        self.y_pixels = self.model.CameraParameters['y_pixels']
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        # Initialize Exposure and Display Information - Convert from milliseconds to seconds.
        self.camera_line_interval = self.model.CameraParameters['line_interval']
        self.camera_exposure_time = self.model.CameraParameters['exposure_time'] / 1000
        self.camera_display_live_subsampling = self.model.CameraParameters[
            'display_live_subsampling']
        self.camera_display_acquisition_subsampling = self.model.CameraParameters[
            'display_acquisition_subsampling']

    def __del__(self):
        pass

    def stop(self):
        pass

    def report_settings(self):
        pass

    def close_camera(self):
        pass

    def set_sensor_mode(self, mode):
        pass

    def set_exposure_time(self, time):
        pass

    def set_line_interval(self, time):
        pass

    def set_binning(self, binningstring):
        pass

    def initialize_image_series(self):
        pass

    def get_images_in_series(self):
        pass

    def close_image_series(self):
        pass

    def get_image(self):
        pass

    def initialize_live_mode(self):
        pass

    def get_live_image(self):
        pass

    def close_live_mode(self):
        pass


class SyntheticCamera(CameraBase):
    def __init__(self, camera_id, model, experiment, verbose=False):
        super().__init__(camera_id, model, experiment, verbose)
        
        self.x_pixels = experiment.CameraParameters['x_pixels']
        self.y_pixels = experiment.CameraParameters['y_pixels']
        
        if self.verbose:
            print("Synthetic Camera Class Initialized")

    def __del__(self):
        pass

    def stop(self):
        self.stop_flag = True

    def report_settings(self):
        pass

    def close_camera(self):
        pass

    def set_sensor_mode(self, mode):
        pass

    def set_exposure_time(self, exposure_time):
        self.camera_exposure_time = exposure_time

    def set_line_interval(self, line_interval_time):
        pass

    def set_binning(self, binning_string):
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        self.data_buffer = data_buffer
        self.num_of_frame = number_of_frames
        self.current_frame_idx = 0
        self.pre_frame_idx = 0

    def get_images_in_series(self):
        images = []
        for i in range(10):
            images.append(
                np.random.randint(
                    low=255,
                    size=(
                        self.x_pixels,
                        self.y_pixels),
                    dtype=np.uint16))
        return images

    def close_image_series(self):
        pass

    def get_image(self):
        image = np.random.normal(1000, 400, (self.y_pixels, self.x_pixels))
        image = np.around(image)
        time.sleep(self.camera_exposure_time / 1000)
        return image

    def initialize_live_mode(self):
        pass

    def get_live_image(self):
        images = []
        for i in range(10):
            images.append(
                np.random.randint(
                    low=255,
                    size=(
                        self.x_pixels,
                        self.y_pixels),
                    dtype=np.uint16))
        return images

    def close_live_mode(self):
        pass

    def generate_new_frame(self):
        image = np.random.randint(
            low=255,
            size=(
                self.x_pixels,
                self.y_pixels),
            dtype=np.uint16)
        ctypes.memmove(self.data_buffer[self.current_frame_idx].ctypes.data,
                       image.ctypes.data, self.x_pixels * self.y_pixels * 2)
        self.current_frame_idx = (
            self.current_frame_idx + 1) % self.num_of_frame

    def get_new_frame(self):
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
        if self.verbose:
            print('get a new frame from camera', frames)
        return frames

    def set_ROI(self, roi_height=2048, roi_width=2048):
        self.x_pixels = roi_width
        self.y_pixels = roi_height

    def get_minimum_waiting_time(self):
        return 0.01


class HamamatsuOrca(CameraBase):

    def __init__(self, camera_id, model, experiment, verbose=False):
        super().__init__(camera_id, model, experiment, verbose)

        # Locally Import Hamamatsu API and Initialize Camera Controller
        HamamatsuController = importlib.import_module('model.devices.APIs.hamamatsu.HamamatsuAPI')
        self.camera_controller = HamamatsuController.DCAM(camera_id)

        # Values are pulled from the CameraParameters section of the configuration.yml file.
        # Exposure time converted here from milliseconds to seconds.
        self.camera_controller.set_property_value(
            "sensor_mode", 1)

        # self.camera_controller.set_property_value(
        #     "sensor_mode", self.model.CameraParameters['sensor_mode'])
        self.camera_controller.set_property_value(
            "defect_correct_mode",
            self.model.CameraParameters['defect_correct_mode'])
        # self.camera_controller.set_property_value("exposure_control",
        #                                           1)
        self.camera_controller.set_property_value(
            "binning", int(self.model.CameraParameters['binning'][0]))
        self.camera_controller.set_property_value(
            "readout_speed", self.model.CameraParameters['readout_speed'])
        self.camera_controller.set_property_value(
            "trigger_active", self.model.CameraParameters['trigger_active'])
        self.camera_controller.set_property_value(
            "trigger_mode", self.model.CameraParameters['trigger_mode'])
        self.camera_controller.set_property_value(
            "trigger_polarity", self.model.CameraParameters['trigger_polarity'])
        self.camera_controller.set_property_value(
            "trigger_source", self.model.CameraParameters['trigger_source'])
        self.camera_controller.set_property_value(
            "exposure_time", self.model.CameraParameters['exposure_time'] / 1000)
        self.camera_controller.set_property_value(
            "internal_line_interval",
            self.model.CameraParameters['line_interval'])
        # 05/16 Debugging
        # self.set_ROI(experiment.CameraParameters['x_pixels'], experiment.CameraParameters['y_pixels'])
        # self.camera_controller.set_property_value("image_height",
        #                                           self.model.CameraParameters['y_pixels'])
        # self.camera_controller.set_property_value("image_width",
        #                                           self.model.CameraParameters['x_pixels'])

        if self.verbose:
            print("Hamamatsu Camera Class Initialized")

    def __del__(self):
        self.camera_controller.dev_close()
        if self.verbose:
            print("Hamamatsu Camera Shutdown")

    def stop(self):
        self.stop_flag = True

    def report_settings(self):
        params = ["defect_correct_mode",
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
                  "exposure_time"]
        for param in params:
            print(param, self.camera_controller.get_property_value(param))

    def close_camera(self):
        self.camera_controller.shutdown()

    def set_sensor_mode(self, mode):
        if mode == 'Normal':
            self.camera_controller.set_property_value("sensor_mode", 1)
        elif mode == 'Light-Sheet':
            self.camera_controller.set_property_value("sensor_mode", 12)
        else:
            print('Camera mode not supported')

    def set_readout_direction(self, mode):
        if mode == 'Top-to-Bottom':
            #  'Forward' readout direction
            self.camera_controller.set_property_value("readout_direction", 1)
        elif mode == 'Bottom-to-Top':
            #  'Backward' readout direction
            self.camera_controller.set_property_value("readout_direction", 2)
        elif mode == 'bytrigger':
            self.camera_controller.set_property_value("readout_direction", 3)
        elif mode == 'diverge':
            self.camera_controller.set_property_value("readout_direction", 4)
        else:
            print('Camera readout direction not supported')

    def set_lightsheet_rolling_shutter_width(self, mode):
        # TODO: Figure out how to do this.  I believe it is dictated by the exposure time and the line interval.
        pass

    def calculate_readout_time(self):
        """
        # Calculates the readout time and maximum frame rate according to the camera configuration settings.
        # Assumes model C13440 with Camera Link communication from Hamamatsu.
        # Currently pulling values directly from the camera.
        """
        h = 9.74436 * 10 ** -6  # Readout timing constant
        vn = self.camera_controller.get_property_value('subarray_vsize')
        sensor_mode = self.camera_controller.get_property_value('sensor_mode')
        exposure_time = self.camera_controller.get_property_value('exposure_time')
        trigger_source = self.camera_controller.get_property_value('trigger_source')
        trigger_active = self.camera_controller.get_property_value('trigger_active')

        if sensor_mode == 1:
            #  Area sensor mode operation
            if trigger_source == 1:
                # Internal Trigger Source
                max_frame_rate = 1 / ((vn/2)*h)
                readout_time = exposure_time - ((vn/2)*h)

            if trigger_active == 1 or 2:
                #  External Trigger Source
                #  Edge == 1, Level == 2
                max_frame_rate = 1 / ((vn/2) * h + exposure_time + 10*h)
                readout_time = exposure_time - ((vn/2) * h + exposure_time + 10*h)

            if trigger_active == 3:
                #  External Trigger Source
                #  Synchronous Readout == 3
                max_frame_rate = 1 / ((vn/2) * h + 5*h)
                readout_time = exposure_time - ((vn/2) * h + 5*h)

        if sensor_mode == 12:
            #  Progressive sensor mode operation
            max_frame_rate = 1 / (exposure_time + (vn+10)*h)
            readout_time = exposure_time - 1 / (exposure_time + (vn+10)*h)

        return readout_time, max_frame_rate


    def set_exposure_time(self, exposure_time):
        """
        #  Units of the Hamamatsu API are in seconds.
        #  All of our units are in milliseconds.
        #  Must convert to seconds.
        """
        exposure_time = exposure_time / 1000
        self.camera_controller.set_property_value(
            "exposure_time", exposure_time)

    def set_line_interval(self, line_interval_time):
        self.camera_controller.set_property_value(
            "internal_line_interval", line_interval_time)

    def set_binning(self, binning_string):
        self.camera_controller.set_property_value("binning", binning_string)
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        self.experiment.CameraParameters['camera_binning'] = str(
            self.x_binning) + 'x' + str(self.y_binning)

    def set_ROI(self, roi_height=2048, roi_width=2048):
        """
        # Change the size of the region of interest on the camera.
        """
        # Get the Maximum Number of Pixels from the Configuration File
        camera_height = self.model.CameraParameters['y_pixels']
        camera_width = self.model.CameraParameters['x_pixels']

        # Calculate Location of Image Edges
        roi_top = (camera_height - roi_height) / 2
        roi_bottom = roi_top + roi_height - 1
        roi_left = (camera_width - roi_width) / 2
        roi_right = roi_left + roi_width - 1

        # Set ROI
        self.x_pixels, self.y_pixels = self.camera_controller.set_ROI(
            roi_left, roi_top, roi_right, roi_bottom)

        if self.verbose:
            print(
                "subarray_hpos",
                self.camera_controller.get_property_value('subarray_hpos'))
            print(
                "subarray_hsize",
                self.camera_controller.get_property_value('subarray_hsize'))
            print(
                "subarray_vpos",
                self.camera_controller.get_property_value('subarray_vpos'))
            print(
                "subarray_vsize",
                self.camera_controller.get_property_value('subarray_vsize'))

            print('sub array mode(1: OFF, 2: ON): ',
                  self.camera_controller.get_property_value('subarray_mode'))

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        self.camera_controller.start_acquisition(data_buffer, number_of_frames)

    def close_image_series(self):
        self.camera_controller.stop_acquisition()

    def initialize_live_mode(self):
        # self.camera_controller.setACQMode(mode="run_till_abort")
        self.camera_controller.start_acquisition()

    def close_live_mode(self):
        self.camera_controller.stop_acquisition()

        # self.running = False
        # self.mode = self.MODE_SINGLE_SHOT

    def get_new_frame(self):
        return self.camera_controller.get_frames()

    def get_minimum_waiting_time(self):
        '''
        # this function will get timings from the camera device
        # cyclic_trigger_period, minimum_trigger_blank, minimum_trigger_interval
        # 'cyclic_trigger_period' of current device is 0
        # according to the document, trigger_blank should be bigger than trigger_interval.
        '''
        try:
            # cyclic_trigger = self.camera_controller.get_property_value('cyclic_trigger_period')
            trigger_blank = self.camera_controller.get_property_value('minimum_trigger_blank')
            trigger_interval = self.camera_controller.get_property_value('minimum_trigger_interval')
        except:
            trigger_blank = 0.016
            trigger_interval = 0.037
        return trigger_blank + trigger_interval