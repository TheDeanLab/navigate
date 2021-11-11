# Standard Python libraries
import queue
import time
import os
import atexit
import threading
#from multiprocessing import shared_memory

# External libraries
import numpy as np
from tifffile import imread, imwrite

# Import Concurrency Classes
#TODO: Relative import with no known parent package error...
from .controller.concurrency import concurrency_tools as ct
from .controller.concurrency import acquisition_array_class as acq_arrays

# Import Hardware Classes
from camera import dcam as Dcam
from daq import WaveFormGenerator as waveform_generator
from filter_wheel import Lambda10B as filter_wheel
from lasers import LuxxLaser as luxx_laser
from lasers import ObisLaser as obis_laser
from stages import PIStage as pi_stage

from .config.constants import AcquisitionHardware
from .config.constants import ASLMParameters
from .config.constants import StageParameters
from .config.constants import ZoomParameters
from .config.constants import FilterWheelParameters
from .config.constants import CameraParameters

class ASLMModel:
    def __init__(self):
        """
        We use bytes_per_buffer to specify the shared_memory_sizes for the
        child processes.
        """
        self.verbose = True
        self.unfinished_tasks = queue.Queue()
        self.num_frames = 0
        self.initial_time = time.perf_counter()

        # Initialize Microscope Parameters
        self.exposure_time_HR = CameraParameters.exposure_time
        self.exposure_time_LR = CameraParameters.exposure_time
        self.continue_preview_low_res = False
        self.continue_preview_high_res = False
        self.stack_nb_planes_low_res =200
        self.stack_nb_planes_high_res = 200
        self.low_res_plane_spacing = 10000000
        self.high_res_plane_spacing = 10000000
        self.display_im_stack = 1

        self.filepath = 'E:/testimage.tif'
        self.current_laser = AcquisitionHardware.laser_488
        self.channel_indicator = "00"
        self.autoscale_preview = 0
        self.slow_velocity=1
        self.slow_acceleration =1

        # Initialize Pixel Sizes from constants
        self.current_low_res_ROI_width = ZoomParameters.low_res_zoom_pixel_size['1x']
        self.current_low_res_ROI_height = ZoomParameters.low_res_zoom_pixel_size['1x']
        self.current_high_res_ROI_width = ZoomParameters.high_res_zoom_pixel_size
        self.current_high_res_ROI_height = ZoomParameters.high_res_zoom_pixel_size

        #for keeping track of the allocated buffer size (so that it doesn't have to be allocated twice)
        self.update_buffer_hig_hres_width = 0
        self.update_buffer_high_res_height = 0
        self.update_buffer_high_res_stacknb = 0
        self.update_buffer_low_res_width = 0
        self.update_buffer_low_res_height = 0
        self.update_buffer_low_res_stacknb = 0
        self.high_res_memory_names = None
        self.low_res_memory_names = None

        self.delay_camera_trigger = 0.001  # the time given for the stage to move to the new position

        # Initialize ASLM Parameters from constants
        self.ASLM_acquisition_time = ASLMParameters.ASLM_acquisition_time
        self.ASLM_from_volt = ASLMParameters.ASLM_from_volt
        self.ASLM_to_volt = ASLMParameters.ASLM_to_volt
        self.ASLM_current_volt = ASLMParameters.ASLM_current_volt
        self.ASLM_static_low_res_volt = ASLMParameters.low_res_volt
        self.ASLM_static_high_res_volt = ASLMParameters.high_res_volt
        self.ASLM_alignment_on = ASLMParameters.ASLM_alignment_on
        self.ASLM_delay_before_voltage_return = ASLMParameters.ASLM_delay_before_voltage_return
        self.ASLM_additional_return_time = ASLMParameters.ASLM_additional_return_time
        self.ASLM_scan_width = ASLM_parameters.simultaneous_lines

        # Initialize Preview Buffers
        self.low_res_buffer = ct.SharedNDArray(shape=(Camera_parameters.LR_height_pixel, Camera_parameters.LR_width_pixel), dtype='uint16')
        self.high_res_buffer = ct.SharedNDArray(shape=(Camera_parameters.HR_height_pixel, Camera_parameters.HR_width_pixel), dtype='uint16')
        self.low_res_buffer.fill(0) #fill to initialize
        self.high_res_buffer.fill(0) #fill to initialize

        # Text label for GUI
        self.current_frames_per_second = str(0)

        # Update buffers
        self.update_buffer_size()
        self.high_res_buffers_queue = queue.Queue()
        self.low_res_buffers_queue = queue.Queue()
        for i in range(2):
            self.high_res_buffers_queue.put(i)
            self.low_res_buffers_queue.put(i)

        # Start initializing all hardware components here by calling the initialization from a ResultThread
        low_res_camera_init = ct.ResultThread(target=self._init_low_res_camera).start() #~3.6s
        high_res_camera_init = ct.ResultThread(target=self._init_high_res_camera).start() #~3.6s
        self._init_display() #~1.3s

        #init acquisition array writing class
        self.get_acq_array = acq_arrays.acquisition_arrays(self)

        #initialize stages and stages in ResultThreads
        trans_stage_init = ct.ResultThread(target=self._init_XYZ_stage).start() #~0.4s
        rot_stage_init = ct.ResultThread(target=self._init_rotation_stage).start()
        filterwheel_init = ct.ResultThread(target=self._init_filterwheel).start()  # ~5.3s
        slit_init = ct.ResultThread(target=self._init_slit).start()  #


        self._init_ao()  # ~0.2s

        #wait for all started initialization threads before continuing (by calling thread join)
        low_res_camera_init.get_result()
        high_res_camera_init.get_result()
        filterwheel_init.get_result()
        trans_stage_init.get_result()
        rot_stage_init.get_result()
        slit_init.get_result()

        print('Finished initializing multiScope')

    # TODO: Convert the Camera Classes to Hamamatsu
    def _init_low_res_camera(self):
        """ Initialize low resolution camera """
        print("Initializing Low Resolution Camera ..")
        # Place the Photometrics class as object into an Object in Subprocess
        self.low_res_camera = ct.ObjectInSubprocess(HamamatsuCamera.Photo_Camera, 'PMPCIECam00')

        self.low_res_camera_ROI = self.low_res_camera.get_imageroi()
        print(self.low_res_camera_ROI)
        #self.low_res_camera.take_snapshot(20)
        print("Low Resolution Camera Initialized.")

    def _init_high_res_camera(self):
        """ Initialize high resolution camera """
        print("Initializing High Resolution Camera ..")
        #place the Photometrics class as object into an Object in Subprocess
        self.high_res_camera = ct.ObjectInSubprocess(Photometricscamera.Photo_Camera, 'PMUSBCam00')
        self.high_res_camera_ROI = self.high_res_camera.get_imageroi()
        print(self.high_res_camera_ROI)
        #self.low_res_camera.take_snapshot(20)
        print("High Resolution Camera Initialized.")

    def _init_display(self):
        print("Initializing display...")
        self.display = ct.ObjectInSubprocess(napari._NapariDisplay, custom_loop= napari._napari_child_loop, close_method_name='close')

        print("done with display.")

    def _init_ao(self):
        """
        Initialize National Instruments card 6378 as device 1, Dev1
        """
        print("Initializing ao card...", end=' ')

        self.ao = ni.Analog_Out(
            num_channels=NI_board_parameters.ao_nchannels,
            rate=NI_board_parameters.rate,
            daq_type=NI_board_parameters.ao_type,
            line=NI_board_parameters.line_selection,
            verbose=True)

        self.ao_laser488_power = ni.Analog_Out(
            daq_type=NI_board_parameters.ao_type_constant,
            line=NI_board_parameters.power_488_line,
            minVol=NI_board_parameters.minVol_constant,
            maxVol=NI_board_parameters.maxVol_constant,
            verbose=True)
        self.ao_laser552_power = ni.Analog_Out(
            daq_type=NI_board_parameters.ao_type_constant,
            line=NI_board_parameters.power_552_line,
            minVol=NI_board_parameters.minVol_constant,
            maxVol=NI_board_parameters.maxVol_constant,
            verbose=True)
        self.ao_laser594_power = ni.Analog_Out(
            daq_type=NI_board_parameters.ao_type_constant,
            line=NI_board_parameters.power_594_line,
            minVol=NI_board_parameters.minVol_constant,
            maxVol=NI_board_parameters.maxVol_constant,
            verbose=True)
        self.ao_laser640_power = ni.Analog_Out(
            daq_type=NI_board_parameters.ao_type_constant,
            line=NI_board_parameters.power_640_line,
            minVol=NI_board_parameters.minVol_constant,
            maxVol=NI_board_parameters.maxVol_constant,
            verbose=True)
        self.flipMirrorPosition_power = ni.Analog_Out(
            daq_type=NI_board_parameters.ao_type_constant,
            line=NI_board_parameters.flip_mirror_line,
            minVol=NI_board_parameters.minVol_constant,
            maxVol=NI_board_parameters.maxVol_constant,
            verbose=True)
        self.mSPIMmirror_voltage = ni.Analog_Out(
            daq_type=NI_board_parameters.ao_type_constant,
            line=NI_board_parameters.mSPIM_mirror_line,
            minVol=NI_board_parameters.minVol_constant,
            maxVol=NI_board_parameters.max_mSPIM_constant,
            verbose=True)
        self.mSPIMmirror_voltage.setconstantvoltage(0.1)
        print("done with ao.")
        atexit.register(self.ao.close)

    def _init_filterwheel(self):
        """
        Initialize filterwheel
        """
        ComPort = FilterWheel_parameters.comport
        self.filters = FilterWheel_parameters.avail_filters

        print("Initializing filter wheel...", end=' ')
        self.filterwheel = FilterWheel.LudlFilterwheel(ComPort, self.filters)
        self.filterwheel.set_filter('515-30-25', wait_until_done=False)
        self.filterwheel.set_filter('572/20-25', wait_until_done=False)
        self.filterwheel.set_filter('615/20-25', wait_until_done=False)
        self.filterwheel.set_filter('676/37-25', wait_until_done=False)
        print("done with filterwheel.")

    def _init_XYZ_stage(self):
        """
        Initialize translation stage
        """
        print("Initializing XYZ stage usb:sn:MCS2-00001795...")
        stage_id = Stage_parameters.stage_id_XYZ
        self.XYZ_stage = TransStage.SLC_translationstage(stage_id)
        self.XYZ_stage.findReference()
        print("done with XYZ stage.")
        atexit.register(self.XYZ_stage.close)

    def _init_rotation_stage(self):
        """
        Initialize rotation stage
        """
        print("Initializing rotation stage...")
        stage_id = Stage_parameters.stage_id_rot
        self.rotationstage = RotStage.SR2812_rotationstage(stage_id)
        #self.rotationstage.ManualMove()
        print("done with XY stage.")
        atexit.register(self.rotationstage.close)

    def _init_slit(self):
        """
        Initialize motorized slit
        """
        self.adjustableslit = SlitControl.slit_ximc_control()
        self.adjustableslit.slit_info()
        self.adjustableslit.slit_status()
        self.adjustableslit.slit_set_microstep_mode_256()
        self.adjustableslit.home_stage()
        print("slit homed")
        self.adjustableslit.slit_set_speed(1000)

    def update_buffer_size(self):
        """
        This handles the size of the buffers during acquisitions.
        """

        #check for whether some image dimension parameters were changed
        if (self.update_buffer_hig_hres_width != self.current_high_res_ROI_width) or (
                self.update_buffer_high_res_height != self.current_high_res_ROI_height) or (
                self.update_buffer_high_res_stacknb != self.stack_nb_planes_high_res):

            #make sure to delete previous shared memory
            if self.high_res_memory_names != None:
                print("Delete previous shared memory arrays")
                try:
                    shared_memory.SharedMemory(name=self.high_res_memory_names[0]).unlink()
                    shared_memory.SharedMemory(name=self.high_res_memory_names[1]).unlink()
                except FileNotFoundError:
                    pass  # This is the error we expected if the memory was unlinked.

            #allocate memory
            self.high_res_buffers = [ct.SharedNDArray(shape=(self.stack_nb_planes_high_res, self.current_high_res_ROI_height, self.current_high_res_ROI_width), dtype='uint16')
                for i in range(2)]
            self.high_res_buffers[0].fill(0)
            self.high_res_buffers[1].fill(0)

            self.high_res_memory_names = [self.high_res_buffers[i].shared_memory.name for i in range(2)]
            #save current parameters so that you don't have to reallocate the memory again without image dimension changes
            self.update_buffer_hig_hres_width = self.current_high_res_ROI_width
            self.update_buffer_high_res_height = self.current_high_res_ROI_height
            self.update_buffer_high_res_stacknb = self.stack_nb_planes_high_res
            print("high res buffer updated")

        if (self.update_buffer_low_res_width != self.current_low_res_ROI_width) or (
                self.update_buffer_low_res_height != self.current_low_res_ROI_height) or (
                self.update_buffer_low_res_stacknb != self.stack_nb_planes_low_res):

            # make sure to delete previous shared memory
            if self.low_res_memory_names != None:
                print("Delete previous shared memory arrays")
                try:
                    shared_memory.SharedMemory(name=self.low_res_memory_names[0]).unlink()
                    shared_memory.SharedMemory(name=self.low_res_memory_names[1]).unlink()
                except FileNotFoundError:
                    pass  # This is the error we expected if the memory was unlinked.

            self.low_res_buffers = [
                ct.SharedNDArray(shape=(self.stack_nb_planes_low_res, self.current_low_res_ROI_height, self.current_low_res_ROI_width), dtype='uint16')
                for i in range(2)]

            self.low_res_buffers[0].fill(0)
            self.low_res_buffers[1].fill(0)

            self.update_buffer_low_res_width = self.current_low_res_ROI_width
            self.update_buffer_low_res_height = self.current_low_res_ROI_height
            self.update_buffer_low_res_stacknb = self.stack_nb_planes_low_res
            print("low res buffer updated")
            self.low_res_memory_names = [self.high_res_buffers[i].shared_memory.name for i in range(2)]



    def close(self):
        """
        Close all opened channels, camera etc
                """
        self.finish_all_tasks()
        self.low_res_camera.close()
        self.high_res_camera.close()
        self.ao.close()
        self.rotationstage.close()
        self.XYZ_stage.close()
        self.adjustableslit.slit_closing()
        self.display.close()  # more work needed here
        print('Closed multiScope')

    def finish_all_tasks(self):
        collected_tasks = []
        while True:
            try:
                th = self.unfinished_tasks.get_nowait()
            except queue.Empty:
                break
            th.join()
            collected_tasks.append(th)
        return collected_tasks

    def set_laserpower(self, powersettings):
        self.ao_laser488_power.setconstantvoltage(powersettings[0])
        self.ao_laser552_power.setconstantvoltage(powersettings[1])
        self.ao_laser594_power.setconstantvoltage(powersettings[2])
        self.ao_laser640_power.setconstantvoltage(powersettings[3])

    def check_movementboundaries(self, array):
        '''
        :param array = [axialPosition, lateralPosition, updownPosition, anglePosition], a list of position the stages moves to
        :return: an array which has no out of range positions
        '''
        if array[0] > 20 * 1000000000:
            array[0] = 19.9 * 1000000000
        if array[0] < -20 * 1000000000:
            array[0] = -19.9 * 1000000000

        if array[1] > 20 * 1000000000:
            array[1] = 19.9 * 1000000000
        if array[1] < -20 * 1000000000:
            array[1] = -19.9 * 1000000000

        if array[2] > 41.9 * 1000000000:
            array[2] = 41.5 * 1000000000
        if array[2] < -41.9 * 1000000000:
            array[2] = -41.5 * 1000000000

        return array

    def move_to_position(self, positionlist):
        print(str(positionlist[0:3]))
        positionlistInt = np.array(positionlist, dtype=np.int64)
        self.XYZ_stage.moveToPosition(positionlistInt[0:3])
        self.rotationstage.moveToAngle(positionlist[3])

    def move_adjustableslit(self, slitopening, wait=0):
        """
        :param slitopening: move to this slitopening;
        :param if wait==1 - wait for slit move to finish before continuing
        """
        self.adjustableslit.slit_move(int(slitopening),0)
        if wait==1:
            self.adjustableslit.slit_wait_for_stop(100)



    def changeLRtoHR(self):
        """
        change from low resolution to high resolution acquisition settings
        """
        self.flipMirrorPosition_power.setconstantvoltage(3)
        self.move_adjustableslit(self.slitopening_high_res, 1)


    def changeHRtoLR(self):
        """
        change from high resolution to low resolution acquisition settings
        """
        self.flipMirrorPosition_power.setconstantvoltage(0)
        self.move_adjustableslit(self.slitopening_low_res, 1)

    ### ---------------------------below here are the preview functions -----------------------------------------------

    def preview_low_res(self):
        """
        starts a custody thread to run a low resolution preview.
        """
        def preview_low_res_task(custody):

            self.num_frames = 0
            self.initial_time = time.perf_counter()

            def laser_preview():
                while self.continue_preview_low_res:
                    basic_unit = self.get_acq_array.get_low_res_preview_array()
                    self.ao.verbose == False
                    self.ao.play_voltages(basic_unit, block=True)


            ct.ResultThread(target=laser_preview).start()

            while self.continue_preview_low_res:
                self.low_res_camera.set_up_low_res_preview(self.exposure_time_LR)

                custody.switch_from(None, to=self.low_res_camera)
                self.low_res_camera.run_preview(out=self.low_res_buffer)

                #display
                custody.switch_from(self.low_res_camera, to=self.display)
                self.display.show_image_low_res(self.low_res_buffer)

                if self.autoscale_preview == 1:
                    minval = np.amin(self.low_res_buffer)
                    maxval = np.amax(self.low_res_buffer)
                    self.display.set_contrast(minval, maxval, "low_respreview")
                    print("updated preview settings")

                custody.switch_from(self.display, to=None)
                self.num_frames += 1
                #calculate fps to display
                if self.num_frames == 100:
                    time_elapsed = time.perf_counter() - self.initial_time
                    print("%0.2f average FPS" % (self.num_frames / time_elapsed))
                    self.num_frames = 0
                    self.initial_time = time.perf_counter()

            self.low_res_camera.end_preview()

        self.low_res_buffer = ct.SharedNDArray(shape=(self.current_low_res_ROI_height, self.current_low_res_ROI_width), dtype='uint16')
        self.continue_preview_low_res = True
        th = ct.CustodyThread(target=preview_low_res_task, first_resource=None)
        th.start()
        return th

    # this is the code to run a high resolution preview with a static light-sheet
    def preview_high_res_static(self):
        def preview_high_res_task(custody):

            self.num_frames = 0
            self.initial_time = time.perf_counter()

            def laser_preview_high_res():
                #old_laserline = 0
                while self.continue_preview_high_res:
                    basic_unit = self.get_acq_array.get_high_res_preview_array()
                    self.ao.play_voltages(basic_unit, block=True)

            #run laser as sub-thread that is terminated when the preview button is pressed (self.continue_preview_high_res is false).
            ct.ResultThread(target=laser_preview_high_res).start()

            while self.continue_preview_high_res:
                self.high_res_camera.set_up_high_respreview(self.exposure_time_HR)
                self.num_frames += 1
                custody.switch_from(None, to=self.high_res_camera)
                self.high_res_camera.run_preview(out=self.high_res_buffer)

                #display acquired image
                custody.switch_from(self.high_res_camera, to=self.display)
                self.display.show_image_high_res(self.high_res_buffer)

                if self.autoscale_preview == 1:
                    minval = np.amin(self.high_res_buffer)
                    maxval = np.amax(self.high_res_buffer)
                    self.display.set_contrast(minval, maxval, "high_respreview")

                custody.switch_from(self.display, to=None)

                if self.num_frames == 100:
                    time_elapsed = time.perf_counter() - self.initial_time
                    average_frames_per_second = (self.num_frames / time_elapsed)
                    print("%0.2f average FPS" % average_frames_per_second)
                    self.current_frames_per_second = str(average_frames_per_second)
                    self.num_frames = 0
                    self.initial_time = time.perf_counter()

            self.high_res_camera.end_preview()

        self.high_res_buffer = ct.SharedNDArray(shape=(self.current_high_res_ROI_height, self.current_high_res_ROI_width), dtype='uint16')
        self.continue_preview_high_res = True
        th = ct.CustodyThread(target=preview_high_res_task, first_resource=self.high_res_camera)
        th.start()
        return th

    def calculate_ASLMparameters(self, desired_exposure_time):
        """
        calculate the parameters for an ASLM acquisition
        :param desired_exposure_time: the exposure time that is desired for the whole acquisition
        :return: set the important parameters for ASLM acquisitions
        """
        linedelay = Camera_parameters.high_res_line_digitization_time
        nbrows = self.current_high_res_ROI_height
        self.ASLM_lineExposure = int(np.ceil(desired_exposure_time / (1 + nbrows/self.ASLM_scan_width)))
        self.ASLM_line_delay = int(np.ceil((desired_exposure_time - self.ASLM_lineExposure)/(nbrows *linedelay))) - 1
        self.ASLM_acquisition_time = (self.ASLM_line_delay + 1) * nbrows * linedelay + self.ASLM_lineExposure + (self.ASLM_line_delay +1) *linedelay

        print("ASLM parameters are: {} exposure time, and {} line delay factor, {} total acquisition time for {} scan width".format(self.ASLM_lineExposure, self.ASLM_line_delay, self.ASLM_acquisition_time, self.ASLM_scan_width))

    def preview_high_res_ASLM(self):
        def preview_high_resASLM_task(custody):

            self.num_frames = 0
            self.initial_time = time.perf_counter()

            while self.continue_preview_high_res:

                #calculate ALSM parameters
                self.calculate_ASLMparameters(self.exposure_time_HR)
                self.high_res_camera.prepare_ASLM_acquisition(self.ASLM_lineExposure, self.ASLM_line_delay)

                #generate acquisition array
                basic_unit = self.get_acq_array.get_high_resASLM_preview_array()
                print("array generated")

                custody.switch_from(None, to=self.high_res_camera)

                # write voltages, indicate "False" so that the voltages are not set back to zero at the end (for the remote mirror)
                write_voltages_thread = ct.ResultThread(target=self.ao._write_voltages, args=(basic_unit,False),
                                                        ).start()

                #start camera thread to poll for new images
                def start_camera_streamASLMpreview():
                    self.high_res_camera.run_preview_ASLM(out=self.high_res_buffer)

                camera_stream_thread_ASLMpreview = ct.ResultThread(target=start_camera_streamASLMpreview).start()

                #play voltages
                self.ao.play_voltages(block=True, force_final_zeros=False)

                print("voltages played")
                camera_stream_thread_ASLMpreview.get_result()
                print("camera thread returned")
                self.num_frames += 1

                #display
                custody.switch_from(self.high_res_camera, to=self.display)
                self.display.show_image_high_res(self.high_res_buffer)

                if self.autoscale_preview == 1:
                    minval = np.amin(self.high_res_buffer)
                    maxval = np.amax(self.high_res_buffer)
                    self.display.set_contrast(minval, maxval, "high_respreview")

                custody.switch_from(self.display, to=None)


                if self.num_frames == 100:
                    time_elapsed = time.perf_counter() - self.initial_time
                    print("%0.2f average FPS" % (self.num_frames / time_elapsed))
                    self.num_frames = 0
                    self.initial_time = time.perf_counter()

            #end preview by setting voltages back to zero
            end_unit = np.zeros((100, NI_board_parameters.ao_nchannels), np.dtype(np.float64))
            self.ao.play_voltages(voltages=end_unit, block=True, force_final_zeros=False)

            self.high_res_camera.end_preview()

        self.high_res_buffer = ct.SharedNDArray(shape=(self.current_high_res_ROI_height, self.current_high_res_ROI_width), dtype='uint16')

        #parameters for preview
        self.continue_preview_high_res = True

        #start preview custody thread
        th = ct.CustodyThread(target=preview_high_resASLM_task, first_resource=self.high_res_camera)
        th.start()
        return th

    ### ---------------------------below here are the stack acquisition functions --------------------------------

    def stack_acquisition_master(self, current_folder, current_startposition, whichlaser, resolutionmode):
        """
        Master to start stack acquisitions of different channels and resolution modes. Decides which stack acquisition method to call
        :param current_folder: folder to save the acquired data
        :param current_startposition: start position for the stack streaming
        :param whichlaser: which channels to image
        :return:
        """
        if whichlaser[0]==1:
            print("acquire 488 laser")
            # filepath
            current_filepath = os.path.join(current_folder, "1_CH488_000000.tif")
            if resolutionmode == "low":
                self.acquire_stack_low_res(current_startposition, NI_board_parameters.laser488, current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser488, current_filepath, "ASLM")
            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser488, current_filepath, "SPIM")


        if whichlaser[1]==1:
            print("acquire 552 laser")
            current_filepath = os.path.join(current_folder, "1_CH552_000000.tif")
            if resolutionmode == "low":
                self.acquire_stack_low_res(current_startposition, NI_board_parameters.laser552,
                                            current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser552, current_filepath, "ASLM")
            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser552, current_filepath, "SPIM")


        if whichlaser[2]==1:
            print("acquire 594 laser")
            current_filepath = os.path.join(current_folder, "1_CH594_000000.tif")
            if resolutionmode == "low":
                self.acquire_stack_low_res(current_startposition, NI_board_parameters.laser594,
                                            current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser594, current_filepath, "ASLM")

            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser594, current_filepath, "SPIM")

        if whichlaser[3]==1:
            print("acquire 640 laser")
            current_filepath = os.path.join(current_folder, "1_CH640_000000.tif")
            if resolutionmode == "low":
                self.acquire_stack_low_res(current_startposition, NI_board_parameters.laser640,
                                            current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser640, current_filepath, "ASLM")
            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_high_res(current_startposition, NI_board_parameters.laser640, current_filepath, "SPIM")


    def prepare_acquisition(self, current_startposition, laser):
        """
        prepare acquisition by moving filter wheel and stage system to the correct position
        """
        def movestage():
            self.move_to_position(current_startposition)
        thread_stagemove = ct.ResultThread(target=movestage).start()

        if laser == NI_board_parameters.laser488:
            self.filterwheel.set_filter('515-30-25', wait_until_done=False)
        if laser == NI_board_parameters.laser552:
            self.filterwheel.set_filter('572/20-25', wait_until_done=False)
        if laser == NI_board_parameters.laser594:
            self.filterwheel.set_filter('615/20-25', wait_until_done=False)
        if laser == NI_board_parameters.laser640:
            self.filterwheel.set_filter('676/37-25', wait_until_done=False)

        self.update_buffer_size()

        thread_stagemove.get_result()

    def acquire_stack_low_res(self, current_startposition, current_laserline, filepath):
        def acquire_task(custody):

            custody.switch_from(None, to=self.low_res_camera)

            # prepare acquisition by moving filter wheel and stage, and set buffer size
            self.prepare_acquisition(current_startposition, current_laserline)

            # prepare camera for stack acquisition - put in thread so that program executes faster :)
            def prepare_camera():
                self.low_res_camera.prepare_stack_acquisition(self.exposure_time_LR)
            camera_prepare_thread = ct.ResultThread(target=prepare_camera).start()

            #define NI board voltage array
            basic_unit = self.get_acq_array.get_low_res_StackAq_array(current_laserline)
            control_array = np.tile(basic_unit, (self.stack_nb_planes_low_res + 1, 1))  # add +1 as you want to return to origin position

            #write voltages
            write_voltages_thread = ct.ResultThread(target=self.ao._write_voltages, args=(control_array,),
                                            ).start()

            #set up stage
            self.XYZ_stage.streamStackAcquisition_externalTrigger_setup(self.stack_nb_planes_low_res, self.low_res_plane_spacing, self.slow_velocity, self.slow_acceleration)

            #wait for camera set up before proceeding
            camera_prepare_thread.get_result()

            # start thread on stage to wait for trigger
            def start_stage_stream():
                self.XYZ_stage.streamStackAcquisition_externalTrigger_waitEnd()
            stream_thread = ct.ResultThread(target=start_stage_stream).start()  # ~3.6s

            def start_camera_streamfast():
                self.low_res_camera.run_stack_acquisition_buffer_fast(self.stack_nb_planes_low_res, self.low_res_buffers[current_bufferiter])
                return
            start_camera_streamfast_thread = ct.ResultThread(target=start_camera_streamfast).start()

            # play voltages - you need to use "block true" as otherwise the program finishes without playing the voltages
            self.ao.play_voltages(block=True)

            stream_thread.get_result()
            start_camera_streamfast_thread.get_result()

            custody.switch_from(self.low_res_camera, to=self.display)

            def saveimage():
                # save image
                try:
                    imwrite(filepath, self.low_res_buffers[current_bufferiter])
                except:
                    print("couldn't save image")
            savethread = ct.ResultThread(target=saveimage).start()

            if self.display_im_stack ==1:
                self.display.show_stack(self.low_res_buffers[current_bufferiter])

            def calculate_projection():
                #calculate projections
                t0 = time.perf_counter()
                maxproj_xy = np.max(self.low_res_buffers[current_bufferiter], axis=0)
                maxproj_xz = np.max(self.low_res_buffers[current_bufferiter], axis=1)
                maxproj_yz = np.max(self.low_res_buffers[current_bufferiter], axis=2)
                t1 = time.perf_counter() - t0

                print("time: " + str(t1))

                ##display max projection
                all_proj = np.zeros([self.current_low_res_ROI_height + self.stack_nb_planes_low_res,
                                     self.current_low_res_ROI_width + self.stack_nb_planes_low_res])

                all_proj[0:self.current_low_res_ROI_height, 0:self.current_low_res_ROI_width] = maxproj_xy
                all_proj[self.current_low_res_ROI_height:, 0:self.current_low_res_ROI_width] = maxproj_xz
                all_proj[0:self.current_low_res_ROI_height, self.current_low_res_ROI_width:] = np.transpose(maxproj_yz)

                self.display.show_maxproj(all_proj)
            projection_thread = ct.ResultThread(target=calculate_projection).start()

            custody.switch_from(self.display, to=None)
            #savethread.get_result()
            #projection_thread.get_result()
            return

        ##navigate buffer queue - where to save current image: this allows you to acquire another stack, while the stack before is still being processed
        current_bufferiter = self.low_res_buffers_queue.get()  # get current buffer iter
        self.low_res_buffers_queue.put(current_bufferiter)  # add number to end of queue

        acquire_thread = ct.CustodyThread(
            target=acquire_task, first_resource=self.low_res_camera).start()
        acquire_thread.get_result()

    def acquire_stack_high_res(self, current_startposition, current_laserline, filepath, modality):
        def acquire_taskhigh_resSPIM(custody):
            print("start")
            custody.switch_from(None, to=self.high_res_camera)

            # prepare acquisition by moving filter wheel etc
            self.prepare_acquisition(current_startposition, current_laserline)

            if modality=="ASLM":
                # obtain ASLM parameters
                self.calculate_ASLMparameters(self.exposure_time_HR)

                # define NI board voltage array
                basic_unit = self.get_acq_array.get_high_resASLM_StackAq_array(current_laserline)
                control_array = np.tile(basic_unit, (
                self.stack_nb_planes_high_res + 1, 1))  # add +1 as you want to return to origin position

                # smooth remote mirror voltage
                control_array[:, NI_board_parameters.voicecoil] = self.smooth_sawtooth(
                    control_array[:, NI_board_parameters.voicecoil],
                    window_len=self.ao.s2p(0.002))
                print("voltage array calculated")

                # prepare high res camera for stack acquisition
                self.high_res_camera.prepare_ASLM_acquisition(self.ASLM_lineExposure, self.ASLM_line_delay)
            else:
                # define NI board voltage array
                basic_unit = self.get_acq_array.get_high_resSPIM_StackAq_array(current_laserline)
                control_array = np.tile(basic_unit,
                                        (self.stack_nb_planes_high_res + 1,
                                         1))  # add +1 as you want to return to origin position

                # prepare high res camera for stack acquisition
                self.high_res_camera.prepare_stack_acquisition_high_res(self.exposure_time_HR)
                print("camera initialized")

            # write voltages
            write_voltages_thread = ct.ResultThread(target=self.ao._write_voltages, args=(control_array,),
                                                    ).start()

            # set up stage
            self.XYZ_stage.streamStackAcquisition_externalTrigger_setup(self.stack_nb_planes_high_res, self.high_res_plane_spacing, self.slow_velocity, self.slow_acceleration)

            # start thread on stage to wait for trigger
            def start_stage_streamhigh_resSPIM():
                self.XYZ_stage.streamStackAcquisition_externalTrigger_waitEnd()
            stream_thread = ct.ResultThread(target=start_stage_streamhigh_resSPIM).start()  # ~3.6s

            def start_camera_streamhigh_resSPIM():
                self.high_res_camera.run_stack_acquisition_buffer_fast(self.stack_nb_planes_high_res,
                                                                     self.high_res_buffers[current_bufferiter])
                return

            start_high_rescamera_stream_thread = ct.ResultThread(target=start_camera_streamhigh_resSPIM).start()


            print("stage and camera threads waiting ...")

            # play voltages
            # you need to use "block true" as otherwise the program finishes without playing the voltages really
            self.ao.play_voltages(block=True)

            stream_thread.get_result()
            start_high_rescamera_stream_thread.get_result()

            custody.switch_from(self.high_res_camera, to=self.display)

            def saveimage_high_resSPIM():
                # save image
                try:
                    imwrite(filepath, self.high_res_buffers[current_bufferiter])
                except:
                    print("couldn't save image")
            savethread = ct.ResultThread(target=saveimage_high_resSPIM).start()

            if self.display_im_stack ==1:
                self.display.show_stack(self.high_res_buffers[current_bufferiter])

            def calculate_projection_high_res():
                #calculate projections
                t0 = time.perf_counter()
                maxproj_xy = np.max(self.high_res_buffers[current_bufferiter], axis=0)
                maxproj_xz = np.max(self.high_res_buffers[current_bufferiter], axis=1)
                maxproj_yz = np.max(self.high_res_buffers[current_bufferiter], axis=2)
                t1 = time.perf_counter() - t0

                print("time: " + str(t1))

                ##display max projection
                all_proj = np.zeros([self.current_high_res_ROI_height + self.stack_nb_planes_high_res,
                                     self.current_high_res_ROI_width + self.stack_nb_planes_high_res])
                all_proj[0:self.current_high_res_ROI_height, 0:self.current_high_res_ROI_width] = maxproj_xy
                all_proj[self.current_high_res_ROI_height:, 0:self.current_high_res_ROI_width] = maxproj_xz
                all_proj[0:self.current_high_res_ROI_height, self.current_high_res_ROI_width:] = np.transpose(maxproj_yz)

                self.display.show_maxproj(all_proj)
            projection_thread2 = ct.ResultThread(target=calculate_projection_high_res).start()


            custody.switch_from(self.display, to=None)
            #savethread.get_result()

        ##navigate buffer queue - where to save current image.
        current_bufferiter = self.high_res_buffers_queue.get()  # get current buffer iter
        self.high_res_buffers_queue.put(current_bufferiter)  # add number to end of queue

        #start thread and wait for its completion
        acquire_threadhigh_resSPIM = ct.CustodyThread(
            target=acquire_taskhigh_resSPIM, first_resource=self.high_res_camera).start()
        acquire_threadhigh_resSPIM.get_result()


    def smooth_sawtooth(self, array, window_len = 101):

        if (window_len % 2) == 0:
            window_len = window_len + 1
        startwindow = int((window_len - 1) / 2)

        startarray = np.ones(startwindow) * array[0]
        endarray = np.ones(startwindow) * array[-1]

        s = np.r_[startarray, array, endarray] #make array bigger on both sides

        w = np.ones(window_len, 'd') #define a flat window - all values have equal weight

        returnarray = np.convolve(w / w.sum(), s, mode='valid') #convolve with window to smooth

        return returnarray

if __name__ == '__main__':
    # first code to run in the multiscope

    # Create scope object:
    scope = multiScopeModel()
    #close
    scope.close()
