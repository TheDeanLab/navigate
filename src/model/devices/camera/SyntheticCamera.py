
import numpy as np
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
        pass

    def set_line_interval(self, time):
        pass

    def set_binning(self, binningstring):
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

    def initialize_image_series(self):
        pass

    def get_images_in_series(self):
        images = []
        for i in range(10):
            images.append(np.random.randint(low=255, size=(self.x_pixels, self.y_pixels), dtype=np.uint16))
        return images

    def close_image_series(self):
        pass

    def get_image(self):
        image = np.random.normal(size=(self.x_pixels, self.x_pixels))*100
        image = np.around(image).astype('uint16')
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
