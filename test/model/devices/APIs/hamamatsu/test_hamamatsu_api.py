import random
import time
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

    def test_open_and_close_camera(self):
        from aslm.model.devices.APIs.hamamatsu.HamamatsuAPI import DCAM, camReg
        # open camera
        self.open_camera()
        if camReg.maxCameras > 0:
            assert self.camera.__hdcam != 0, "didn't open camera correctly!"
            assert camReg.numCameras == 1, "didn't register camera correctly!"
            self.camera.dev_close()
            assert self.camera.__hdcam == 0, "didn't close camera correctly!"
            assert camReg.numCameras == 0, "didn't register camera correctly!"


    def test_get_and_set_property_value(self):
        from aslm.model.devices.APIs.hamamatsu.HamamatsuAPI import property_dict
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

    def test_ROI(self):
        self.open_camera()

        rects = [(0, 0, 2047, 2047), (512, 512, 1535, 1535), (768, 768, 1279, 1279)]

        for i in range(10):
            r = random.randint(0, len(rects))
            rect = rects[r]
            self.camera.set_ROI(*rect)
            assert self.camera.get_property_value('image_width') == (rect[2]-rect[0]+1), f'ROI Width: {(rect[2]-rect[0]+1)}'
            assert self.camera.get_property_value('image_height') == (rect[3]-rect[1]+1), f'ROI Height: {(rect[3]-rect[1]+1)}'
        

    def test_acquisition(self):
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

        from aslm.model.concurrency.concurrency_tools import SharedNDArray

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
