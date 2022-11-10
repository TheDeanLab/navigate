"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
# """

import pytest

@pytest.mark.hardware
class TestHamamatsuAPI:
    camera = None

    def open_camera(self):
        from aslm.model.devices.APIs.hamamatsu.HamamatsuAPI import DCAM
        # open camera
        for i in range(10):
            try:
                self.camera = DCAM()
                if self.camera.__hdcam != 0:
                    break
                self.camera.dev_close()
            except:
                continue

    def close_camera(self):
        if self.camera != None:
            self.camera.dev_close()

    def test_open_and_close_camera(self):
        from aslm.model.devices.APIs.hamamatsu.HamamatsuAPI import camReg
        # open camera
        self.open_camera()
        if camReg.maxCameras > 0:
            assert self.camera.__hdcam != 0, "didn't open camera correctly!"
            assert camReg.numCameras == 1, "didn't register camera correctly!"
            self.camera.dev_close()
            assert self.camera.__hdcam == 0, "didn't close camera correctly!"
            assert camReg.numCameras == 0, "didn't register camera correctly!"


    def test_get_and_set_property_value(self):
        self.open_camera()

        # set property
        configuration = {
            'subarray_mode': 1,
            'sensor_mode': 12,  # 12 for progressive
            'defect_correct_mode': 2.0,
            'binning': 1.0,
            'readout_speed': 1.0,
            'trigger_active': 1.0,
            'trigger_mode': 1.0,  # external light-sheet mode
            'trigger_polarity': 2.0,  # positive pulse
            'trigger_source': 3.0,  # software
            'exposure_time': 0.02,
            'internal_line_interval': 0.000075
        }
        for k in configuration:
            assert self.camera.set_property_value(k, configuration[k]), f"can't set property{k} with value{configuration[k]}"

        def is_in_range(value, target, precision=100):
            target_min -= target / precision
            target_max += target / precision
            return value > target_min and value < target_max

        # get property
        for k in configuration:
            v = self.camera.get_property_value(k)
            assert is_in_range(v, configuration[k]), f"The value of {k} isn't right!"

        #set a non-exist property
        assert self.camera.set_property_value('non-exist-property', 100) == False, "can't handle non-exist property name"

        self.close_camera()

    def test_ROI(self):
        import random
        self.open_camera()

        rects = [(0, 0, 2047, 2047), (512, 512, 1535, 1535), (768, 768, 1279, 1279)]

        for i in range(10):
            r = random.randint(0, len(rects))
            rect = rects[r]
            self.camera.set_ROI(*rect)
            assert self.camera.get_property_value('image_width') == (rect[2]-rect[0]+1), f'ROI Width: {(rect[2]-rect[0]+1)}'
            assert self.camera.get_property_value('image_height') == (rect[3]-rect[1]+1), f'ROI Height: {(rect[3]-rect[1]+1)}'

        self.close_camera()
        
    
    def test_acquisition(self):
        import random
        import time
        from aslm.model.concurrency.concurrency_tools import SharedNDArray

        self.open_camera()

        configuration = {
            'sensor_mode': 12,  # 12 for progressive
            'defect_correct_mode': 2.0,
            'binning': 1.0,
            'readout_speed': 1.0,
            'trigger_active': 1.0,
            'trigger_mode': 1.0,  # external light-sheet mode
            'trigger_polarity': 2.0,  # positive pulse
            'trigger_source': 3.0,  # software
            'exposure_time': 0.02,
            'internal_line_interval': 0.000075
        }

        for k in configuration:
            self.camera.set_property_value(k, configuration[k])


        number_of_frames = 100

        data_buffer = [SharedNDArray(shape=(2048, 2048), dtype='uint16') for i in range(number_of_frames)]
        self.camera.start_acquisition(data_buffer, number_of_frames)

        assert self.camera.is_acquiring == True, 'camera should start acquiring data!'

        for i in range(10):
            trigger_num = random.randint(0, 30)
            for j in range(trigger_num):
                self.camera.fire_software_trigger()
                time.sleep(configuration['exposure_time'] + 0.005)

            frames = self.camera.get_frames()
            assert len(frames) == trigger_num, 'can not get all the frames back!'

        self.camera.stop_acquisition()
        assert self.camera.is_acquiring == False, 'camera should stop acquiring data!'

        self.close_camera()
