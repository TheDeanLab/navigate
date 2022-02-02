class mesoSPIM_PhotometricsCamera(mesoSPIM_GenericCamera):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('Thread ID at Startup: ' + str(int(QtCore.QThread.currentThreadId())))

    def open_camera(self):
        from pyvcam import pvc
        from pyvcam import constants as const
        from pyvcam.camera import Camera

        self.const = const
        self.pvc = pvc

        pvc.init_pvcam()
        self.pvcam = [cam for cam in Camera.detect_camera()][0]

        self.pvcam.open()
        self.pvcam.speed_table_index = self.cfg.camera_parameters['speed_table_index']
        self.pvcam.exp_mode = self.cfg.camera_parameters['exp_mode']

        logger.info('Camera Vendor Name: ' + str(self.pvcam.get_param(param_id=self.const.PARAM_VENDOR_NAME)))
        logger.info('Camera Product Name: ' + str(self.pvcam.get_param(param_id=self.const.PARAM_PRODUCT_NAME)))
        logger.info('Camera Chip Name: ' + str(self.pvcam.get_param(param_id=self.const.PARAM_CHIP_NAME)))
        logger.info('Camera System Name: ' + str(self.pvcam.get_param(param_id=self.const.PARAM_SYSTEM_NAME)))

        # Exposure mode options: {'Internal Trigger': 1792, 'Edge Trigger': 2304, 'Trigger first': 2048}
        # self.pvcam.set_param(param_id = self.const.PARAM_EXPOSURE_MODE, value = 2304)

        # Exposure out mode options: {'First Row': 0, 'All Rows': 1, 'Any Row': 2, 'Rolling Shutter': 3, 'Line Output': 4}
        # self.pvcam.set_param(param_id = self.const.PARAM_EXPOSE_OUT_MODE, value = 3)

        ''' Setting ASLM parameters '''
        # Scan mode options: {'Auto': 0, 'Line Delay': 1, 'Scan Width': 2}
        self.pvcam.set_param(param_id=self.const.PARAM_SCAN_MODE, value=self.cfg.camera_parameters['scan_mode'])
        # Scan direction options: {'Down': 0, 'Up': 1, 'Down/Up Alternate': 2}
        self.pvcam.set_param(param_id=self.const.PARAM_SCAN_DIRECTION,
                             value=self.cfg.camera_parameters['scan_direction'])
        # 10.26 us x factor
        # factor = 6 equals 71.82 us
        self.pvcam.set_param(param_id=self.const.PARAM_SCAN_LINE_DELAY,
                             value=self.cfg.camera_parameters['scan_line_delay'])
        self.pvcam.set_param(param_id=self.const.PARAM_READOUT_PORT, value=1)
        ''' Setting Binning parameters: '''
        '''
        self.binning_string = self.cfg.camera_parameters['binning'] # Should return a string in the form '2x4'
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])
        '''
        self.pvcam.binning = (self.x_binning, self.y_binning)

        # self.pvcam.set_param(param_id = self.const.PARAM_BINNING_PAR, value = self.y_binning)
        # self.pvcam.set_param(param_id = self.const.PARAM_BINNING_SER, value = self.x_binning)

        # print('Readout port: ', self.pvcam.readout_port)

        """ 
        self.report_pvcam_parameter('PMODE',self.const.PARAM_PMODE)
        self.report_pvcam_parameter('GAIN_INDEX',self.const.PARAM_GAIN_INDEX)
        self.report_pvcam_parameter('GAIN_NAME',self.const.PARAM_GAIN_NAME)
        self.report_pvcam_parameter('READOUT PORT',self.const.PARAM_READOUT_PORT)
        self.report_pvcam_parameter('READOUT TIME',self.const.PARAM_READOUT_TIME)
        self.report_pvcam_parameter('IMAGE FORMAT', self.const.PARAM_IMAGE_FORMAT)
        self.report_pvcam_parameter('SPEED TABLE INDEX', self.const.PARAM_SPDTAB_INDEX)
        self.report_pvcam_parameter('BIT DEPTH', self.const.PARAM_BIT_DEPTH)


        logger.info('P Mode: '+str(self.pvcam.get_param(param_id = self.const.PARAM_PMODE)))
        logger.info('P Mode options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_PMODE)))
        logger.info('Bit depth: '+str(self.pvcam.get_param(param_id = self.const.PARAM_BIT_DEPTH)))
        logger.info('Exposure time resolution: '+str(self.pvcam.get_param(param_id = self.const.PARAM_EXP_RES)))
        logger.info('Exposure time resolution options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_EXP_RES)))
        logger.info('Exposure mode: '+str(self.pvcam.get_param(param_id = self.const.PARAM_EXPOSURE_MODE)))
        logger.info('Exposure mode options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_EXPOSURE_MODE)))
        logger.info('Exposure out mode: '+str(self.pvcam.get_param(param_id = self.const.PARAM_EXPOSE_OUT_MODE)))
        logger.info('Exposure out mode options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_EXPOSE_OUT_MODE)))
        logger.info('Scan mode: '+str(self.pvcam.get_param(param_id = self.const.PARAM_SCAN_MODE)))
        logger.info('Scan mode options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_SCAN_MODE)))
        logger.info('Scan direction: '+str(self.pvcam.get_param(param_id = self.const.PARAM_SCAN_DIRECTION)))
        logger.info('Scan direction options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_SCAN_DIRECTION)))
        logger.info('Line delay: '+str(self.pvcam.get_param(param_id = self.const.PARAM_SCAN_LINE_DELAY)))
        logger.info('Line time: '+str(self.pvcam.get_param(param_id = self.const.PARAM_SCAN_LINE_TIME)))
        logger.info('Binning SER: '+str(self.pvcam.get_param(param_id = self.const.PARAM_BINNING_SER)))
        logger.info('Binning SER options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_BINNING_SER)))
        logger.info('Binning PAR: '+str(self.pvcam.get_param(param_id = self.const.PARAM_BINNING_PAR)))
        logger.info('Binning PAR options: '+str(self.pvcam.read_enum(param_id = self.const.PARAM_BINNING_PAR)))
        """

    def report_pvcam_parameter(self, description, parameter):
        try:
            logger.info(description + ' ' + str(self.pvcam.get_param(param_id=parameter)))
            print(description + ' ' + str(self.pvcam.get_param(param_id=parameter)))
        except:
            pass

        try:
            logger.info(description + ' ' + str(self.pvcam.read_enum(param_id=parameter)))
            print(description + ' ' + str(str(self.pvcam.read_enum(param_id=parameter))))
        except:
            pass

    def close_camera(self):
        self.pvcam.close()
        self.pvc.uninit_pvcam()

    def set_exposure_time(self, time):
        self.camera_exposure_time = time

    def set_line_interval(self, time):
        print('Setting line interval is not implemented, set the interval in the config file')

    def set_binning(self, binningstring):
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        self.pvcam.binning = (self.x_binning, self.y_binning)
        self.state['camera_binning'] = str(self.x_binning) + 'x' + str(self.y_binning)

    def get_image(self):
        return self.pvcam.get_live_frame()

    def initialize_image_series(self):
        ''' The Photometrics cameras expect integer exposure times, otherwise they default to the minimum value '''
        exp_time_ms = int(self.camera_exposure_time * 1000)
        self.pvcam.start_live(exp_time_ms)

    def get_images_in_series(self):
        return [self.pvcam.get_live_frame()]

    def close_image_series(self):
        self.pvcam.stop_live()

    def initialize_live_mode(self):
        ''' The Photometrics cameras expect integer exposure times, otherwise they default to the minimum value '''
        exp_time_ms = int(self.camera_exposure_time * 1000)
        # logger.info('Initializing live mode with exp time: '+str(exp_time_ms))
        self.pvcam.start_live(exp_time_ms)

    def get_live_image(self):
        return [self.pvcam.get_live_frame()]

    def close_live_mode(self):
        self.pvcam.stop_live()
