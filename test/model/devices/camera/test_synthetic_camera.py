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
import unittest

# Third Party Imports
import pytest
import numpy as np

from aslm.model.devices.camera.camera_synthetic import SyntheticCamera
from aslm.model.dummy_model import get_dummy_model

class TestSyntheticCamera(unittest.TestCase):
    r"""Unit Test for FilterWheel Class"""

    def test_synthetic_camera_initialization(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        return True

    def test_synthetic_camera_attributes(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        desired_attributes = ['x_pixels',
                              'y_pixels',
                              'is_acquiring',
                              '_mean_background_count',
                              '_noise_sigma',
                              'blah',
                              'camera_controller',
                              'current_frame_idx',
                              'data_buffer',
                              'num_of_frame',
                              'pre_frame_idx',
]
        for da in desired_attributes:
            assert hasattr(synthetic_camera, da)


    def test_synthetic_camera_wheel_attributes_type(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        desired_attributes = {'x_pixels': int,
                              'y_pixels': int,
                              'is_acquiring': bool,
                              '_mean_background_count': float,
                              '_noise_sigma': np.float64,
                              # 'current_frame_idx': None,
                              # 'data_buffer': None,
                              # 'num_of_frame': None,
                              # 'pre_frame_idx': None,
                              }

        for key in desired_attributes:
            attribute = getattr(synthetic_camera, key)
            #print(key, type(attribute), desired_attributes[key])
            #assert type(attribute) == desired_attributes[key]


    def test_synthetic_camera_methods(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)

        methods = ['stop',
                   'report_settings',
                   'close_camera',
                   'set_sensor_mode',
                   'set_exposure_time',
                   'set_line_interval',
                   'set_binning',
                   'initialize_image_series',
                   'close_image_series',
                   'generate_new_frame',
                   'get_new_frame',
                   'set_ROI',
                   'get_minimum_waiting_time']

        for m in methods:
            assert hasattr(synthetic_camera, m) and callable(getattr(synthetic_camera, m))

    def test_synthetic_camera_wheel_method_calls(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        synthetic_camera.stop()
        synthetic_camera.report_settings()
        synthetic_camera.close_camera()
        synthetic_camera.set_sensor_mode(mode='test')
        synthetic_camera.set_exposure_time(exposure_time=200)
        synthetic_camera.set_line_interval(line_interval_time=1)
        synthetic_camera.set_binning(binning_string='2x2')
        synthetic_camera.initialize_image_series()
        synthetic_camera.close_image_series()
        synthetic_camera.get_new_frame()
        synthetic_camera.set_ROI()
        synthetic_camera.get_minimum_waiting_time()
        pass

    def test_synthetic_camera_stop(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        synthetic_camera.stop_flag = False
        synthetic_camera.stop()
        assert synthetic_camera.stop_flag is True

    def test_synthetic_camera_exposure(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        exposure_time = 200
        synthetic_camera.set_exposure_time(exposure_time=exposure_time)
        assert (exposure_time / 1000) == synthetic_camera.camera_exposure_time

    def test_synthetic_camera_binning(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        x_pixels = synthetic_camera.x_pixels
        synthetic_camera.set_binning(binning_string='2x2')
        assert synthetic_camera.x_binning == 2
        assert synthetic_camera.y_binning == 2
        assert type(synthetic_camera.x_binning) == int
        assert type(synthetic_camera.y_binning) == int
        assert synthetic_camera.x_pixels == x_pixels / 2

    def test_synthetic_camera_initialize_image_series(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        synthetic_camera.initialize_image_series()
        assert synthetic_camera.num_of_frame == 100
        assert synthetic_camera.data_buffer is None
        assert synthetic_camera.current_frame_idx == 0
        assert synthetic_camera.pre_frame_idx == 0
        assert synthetic_camera.camera_controller.is_acquiring is True

    def test_synthetic_camera_close_image_series(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        synthetic_camera.close_image_series()
        assert synthetic_camera.pre_frame_idx == 0
        assert synthetic_camera.current_frame_idx == 0
        assert synthetic_camera.camera_controller.is_acquiring is False

    def test_synthetic_camera_generate_new_frame(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        synthetic_camera.initialize_image_series(data_buffer=100, number_of_frames=100)
        # TODO - get the data buffer to not be type None

    def test_synthetic_camera_get_new_frame(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        synthetic_camera.initialize_image_series(data_buffer=100, number_of_frames=100)
        # synthetic_camera.generate_new_frame()
        # synthetic_camera.get_new_frame()
        # TODO - get the data buffer to not be type None

    def test_synthetic_get_camera_minimum_wating_time(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)

        wait_time = synthetic_camera.get_minimum_waiting_time()
        assert wait_time == 0.01

    def test_synthetic_camera_set_roi(self):
        self.dummy_model = get_dummy_model()
        self.configuration = self.dummy_model.configuration
        self.configuration['experiment'] = self.dummy_model.experiment
        synthetic_camera = SyntheticCamera(configuration=self.configuration,
                                           experiment=self.configuration['experiment'],
                                           camera_id=0)
        synthetic_camera.set_ROI()
        assert synthetic_camera.x_pixels == 2048
        assert synthetic_camera.y_pixels == 2048
        synthetic_camera.set_ROI(roi_height=500, roi_width=700)
        assert synthetic_camera.x_pixels == 700
        assert synthetic_camera.y_pixels == 500



if (__name__ == "__main__"):
    unittest.main()

