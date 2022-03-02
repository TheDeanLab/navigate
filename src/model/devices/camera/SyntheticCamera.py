import time
import numpy as np
import ctypes
from .CameraBase import CameraBase


class Camera(CameraBase):
    def __init__(self, camera_id, model, experiment, verbose=False):
        super().__init__(camera_id, model, experiment, verbose)

        if self.verbose:
            print("Synthetic Camera Class Initialized")

    def __del__(self):
        pass

    def stop(self):
        self.stop_flag = True

    def report_camera_settings(self):
        pass

    def close_camera(self):
        pass

    def set_camera_sensor_mode(self, mode):
        pass

    def set_exposure_time(self, time):
        self.camera_exposure_time = time

    def set_line_interval(self, time):
        pass

    def set_binning(self, binningstring):
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

    def initialize_image_series(self, data_ptr=None):
        self.data_ptr = data_ptr
        self.num_of_frame = len(data_ptr)
        self.current_frame_idx = 0
        self.pre_frame_idx = 0

    def get_images_in_series(self):
        images = []
        for i in range(10):
            images.append(np.random.randint(low=255, size=(self.x_pixels, self.y_pixels), dtype=np.uint16))
        return images

    def close_image_series(self):
        pass

    def get_image(self):
        image = np.random.normal(1000, 400, (self.y_pixels, self.x_pixels))
        image = np.around(image)
        time.sleep(self.camera_exposure_time/1000)
        return image

    def initialize_live_mode(self):
        pass

    def get_live_image(self):
        images = []
        for i in range(10):
            images.append(np.random.randint(low=255, size=(self.x_pixels, self.y_pixels), dtype=np.uint16))
        return images

    def close_live_mode(self):
        pass

    def generate_new_frame(self):
        # time.sleep(self.camera_exposure_time / 1000)
        image = np.random.randint(low=255, size=(self.x_pixels, self.y_pixels), dtype=np.uint16)
        ctypes.memmove(self.data_ptr[self.current_frame_idx], image.ctypes.data, self.x_pixels*self.y_pixels*2)
        self.current_frame_idx = (self.current_frame_idx + 1) % self.num_of_frame

    def get_new_frame(self):
        time.sleep(self.camera_exposure_time / 1000)
        while self.pre_frame_idx == self.current_frame_idx:
            time.sleep(0.001)
        if self.pre_frame_idx < self.current_frame_idx:
            frames = list(range(self.pre_frame_idx, self.current_frame_idx))
        else:
            frames = list(range(self.pre_frame_idx, self.num_of_frame))
            frames += list(range(0, self.current_frame_idx))
        self.pre_frame_idx = self.current_frame_idx
        if self.verbose:
            print('get a new frame from camera', frames)
        return frames
