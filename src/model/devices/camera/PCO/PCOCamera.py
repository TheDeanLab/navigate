class mesoSPIM_PCOCamera(mesoSPIM_GenericCamera):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('Thread ID at Startup: ' + str(int(QtCore.QThread.currentThreadId())))
        logger.info('PCO Cam initialized')

    def open_camera(self):
        import pco
        self.cam = pco.Camera()  # no logging
        # self.cam = pco.Camera(debuglevel='verbose', timestamp='on')

        self.cam.sdk.set_cmos_line_timing('on', self.cfg.camera_parameters['line_interval'])  # 75 us delay
        self.cam.set_exposure_time(self.cfg.camera_parameters['exp_time'])
        # self.cam.sdk.set_cmos_line_exposure_delay(80, 0) # 266 lines = 20 ms / 75 us
        self.cam.configuration = {'trigger': self.cfg.camera_parameters['trigger']}

        line_time = self.cam.sdk.get_cmos_line_timing()['line time']
        lines_exposure = self.cam.sdk.get_cmos_line_exposure_delay()['lines exposure']
        t = self.cam.get_exposure_time()
        # print('Exposure Time: {:9.6f} s'.format(t))
        # print('Line Time: {:9.6f} s'.format(line_time))
        # print('Number of Lines: {:d}'.format(lines_exposure))

        self.cam.record(number_of_images=4, mode='fifo')

    def close_camera(self):
        self.cam.stop()
        self.cam.close()

    def set_exposure_time(self, time):
        self.cam.set_exposure_time(time)
        self.camera_exposure_time = time

    def set_line_interval(self, time):
        print('Setting line interval is not implemented, set the interval in the config file')

    def set_binning(self, binningstring):
        pass

    def get_image(self):
        image, meta = self.cam.image(image_number=-1)
        return image

    def initialize_image_series(self):
        pass

    def get_images_in_series(self):
        image, meta = self.cam.image(image_number=-1)
        return [image]

    def close_image_series(self):
        pass

    def initialize_live_mode(self):
        pass

    def get_live_image(self):
        image, meta = self.cam.image(image_number=-1)
        return [image]

    def close_live_mode(self):
        pass
