
class CameraBase:
    def __init__(self, camera_id, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.camera_id = camera_id
        self.verbose = verbose
        self.stop_flag = False

        # Initialize Pixel Information
        self.x_pixel_size_in_microns = self.model.CameraParameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.model.CameraParameters['y_pixel_size_in_microns']
        self.binning_string = self.model.CameraParameters['binning']
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])
        self.x_pixels = self.model.CameraParameters['x_pixels']
        self.y_pixels = self.model.CameraParameters['y_pixels']
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        # Initialize Exposure and Display Information
        self.camera_line_interval = self.model.CameraParameters['line_interval']
        self.camera_exposure_time = self.model.CameraParameters['exposure_time']/1000  # milliseconds to seconds
        self.camera_display_live_subsampling = self.model.CameraParameters['display_live_subsampling']
        self.camera_display_acquisition_subsampling = self.model.CameraParameters['display_acquisition_subsampling']

    def __del__(self):
        pass

    def stop(self):
        pass

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
