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

# Third Party Imports
import pytest
import numpy as np

from aslm.model.devices.camera.camera_synthetic import SyntheticCamera, SyntheticCameraController

@pytest.fixture(scope='class')
def synthetic_camera(dummy_model):
    dummy_model = dummy_model
    scc = SyntheticCameraController()
    microscope_name = dummy_model.configuration['experiment']['MicroscopeState']['microscope_name']
    synthetic_camera = SyntheticCamera(microscope_name, scc, dummy_model.configuration)
    return synthetic_camera

class TestSyntheticCamera:
    r"""Unit Test for Camera Synthetic Class"""

    @pytest.fixture(autouse=True)
    def _prepare_camera(self, synthetic_camera):
        self.synthetic_camera = synthetic_camera

    def test_synthetic_camera_attributes(self):
        desired_attributes = ['x_pixels',
                              'y_pixels',
                              'is_acquiring',
                              '_mean_background_count',
                              '_noise_sigma',
                              'camera_controller',
                              'current_frame_idx',
                              'data_buffer',
                              'num_of_frame',
                              'pre_frame_idx',
        ]
        for da in desired_attributes:
            assert hasattr(self.synthetic_camera, da)


    def test_synthetic_camera_wheel_attributes_type(self):
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
            attribute = getattr(self.synthetic_camera, key)
            #print(key, type(attribute), desired_attributes[key])
            #assert type(attribute) == desired_attributes[key]


    def test_synthetic_camera_methods(self):
        methods = ['report_settings',
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
            assert hasattr(self.synthetic_camera, m) and callable(getattr(self.synthetic_camera, m))

    def test_synthetic_camera_wheel_method_calls(self):
        self.synthetic_camera.report_settings()
        self.synthetic_camera.close_camera()
        self.synthetic_camera.set_sensor_mode(mode='test')
        self.synthetic_camera.set_exposure_time(exposure_time=200)
        self.synthetic_camera.set_line_interval(line_interval_time=1)
        self.synthetic_camera.set_binning(binning_string='2x2')
        self.synthetic_camera.initialize_image_series()
        self.synthetic_camera.close_image_series()
        self.synthetic_camera.get_new_frame()
        self.synthetic_camera.set_ROI()
        self.synthetic_camera.get_minimum_waiting_time()

    def test_synthetic_camera_exposure(self):
        exposure_time = 200
        self.synthetic_camera.set_exposure_time(exposure_time=exposure_time)
        assert (exposure_time / 1000) == self.synthetic_camera.camera_exposure_time

    def test_synthetic_camera_binning(self):
        x_pixels = self.synthetic_camera.x_pixels
        self.synthetic_camera.set_binning(binning_string='2x2')
        assert self.synthetic_camera.x_binning == 2
        assert self.synthetic_camera.y_binning == 2
        assert type(self.synthetic_camera.x_binning) == int
        assert type(self.synthetic_camera.y_binning) == int
        assert self.synthetic_camera.x_pixels == x_pixels / 2

    def test_synthetic_camera_initialize_image_series(self):
        self.synthetic_camera.initialize_image_series()
        assert self.synthetic_camera.num_of_frame == 100
        assert self.synthetic_camera.data_buffer is None
        assert self.synthetic_camera.current_frame_idx == 0
        assert self.synthetic_camera.pre_frame_idx == 0
        assert self.synthetic_camera.camera_controller.is_acquiring is True

    def test_synthetic_camera_close_image_series(self):
        self.synthetic_camera.close_image_series()
        assert self.synthetic_camera.pre_frame_idx == 0
        assert self.synthetic_camera.current_frame_idx == 0
        assert self.synthetic_camera.camera_controller.is_acquiring is False

    def test_synthetic_camera_acquire_images(self):
        import random
        from aslm.model.concurrency.concurrency_tools import SharedNDArray
        
        number_of_frames = 100
        data_buffer = [SharedNDArray(shape=(2048, 2048), dtype='uint16') for i in range(number_of_frames)]

        self.synthetic_camera.initialize_image_series(data_buffer, number_of_frames)
        
        assert self.synthetic_camera.is_acquiring == True, 'should be acquring'
        
        frame_idx = 0

        for i in range(10):
            frame_num = random.randint(1, 30)
            for j in range(frame_num):
                self.synthetic_camera.generate_new_frame()
            frames = self.synthetic_camera.get_new_frame()
            
            assert len(frames) == frame_num, "frame number isn't right!"
            assert frames[0] == frame_idx, "frame idx isn't right!"

            frame_idx = (frame_idx + frame_num) % number_of_frames

        self.synthetic_camera.close_image_series()
        assert self.synthetic_camera.is_acquiring == False, 'is_acquiring should be False'

    def test_synthetic_get_camera_minimum_wating_time(self):
        wait_time = self.synthetic_camera.get_minimum_waiting_time()
        assert wait_time == 0.01

    def test_synthetic_camera_set_roi(self):
        self.synthetic_camera.set_ROI()
        assert self.synthetic_camera.x_pixels == 2048
        assert self.synthetic_camera.y_pixels == 2048
        self.synthetic_camera.set_ROI(roi_height=500, roi_width=700)
        assert self.synthetic_camera.x_pixels == 700
        assert self.synthetic_camera.y_pixels == 500
