import multiprocessing
import queue
import time
import os
import atexit
import threading
import numpy as np

from multiprocessing import shared_memory
import auxiliary_code.concurrency_tools as ct
import auxiliary_code.napari_in_subprocess as napari
import acquisition_array_class as acq_arrays

import src.camera.Photometrics_camera as Photometricscamera
import src.ni_board.vni as ni
import src.stages.rotation_stage_cmd as RotStage
import src.stages.translation_stage_cmd as TransStage
import src.filter_wheel.ludlcontrol as FilterWheel
import src.slit.slit_cmd as SlitControl

from constants import FilterWheel_parameters
from constants import Stage_parameters
from constants import NI_board_parameters
from constants import Camera_parameters
from constants import ASLM_parameters
from tifffile import imread, imwrite

class multiScopeModel:
    def __init__(
        self
        ):
        """
        We use bytes_per_buffer to specify the shared_memory_sizes for the
        child processes.
        """
        self.unfinished_tasks = queue.Queue()

        # self.data_buffers = [
        #     ct.SharedNDArray(shape=(2960, 5056), dtype='uint16')
        #     for i in range(2)]
        # self.data_buffer_queue = queue.Queue()
        # for i in range(len(self.data_buffers)):
        #     self.data_buffer_queue.put(i)
        # print("Displaying", self.data_buffers[0].shape,
        #       self.data_buffers[0].dtype, 'images.')
        self.num_frames = 0
        self.initial_time = time.perf_counter()

        #parameters
        self.exposure_time_HR = 200
        self.exposure_time_LR = 200
        self.continue_preview_lowres = False
        self.continue_preview_highres = False
        self.stack_nbplanes_lowres =200
        self.stack_nbplanes_highres = 200
        self.lowres_planespacing = 10000000
        self.highres_planespacing = 10000000
        self.displayImStack = 1

        self.filepath = 'D:/acquisitions/testimage.tif'
        self.current_laser = NI_board_parameters.laser488
        self.channelIndicator = "00"
        self.slitopening_lowres = 3700
        self.slitopening_highres= 4558
        self.autoscale_preview = 0
        self.slow_velocity=1
        self.slow_acceleration =1

        self.current_lowresROI_width = Camera_parameters.LR_width_pixel
        self.current_lowresROI_height = Camera_parameters.LR_height_pixel
        self.current_highresROI_width = Camera_parameters.HR_width_pixel
        self.current_highresROI_height = Camera_parameters.HR_height_pixel

        #for keeping track of the allocated buffer size (so that it doesn't have to be allocated twice)
        self.updatebuffer_highres_width = 0
        self.updatebuffer_highres_height = 0
        self.updatebuffer_highres_stacknb = 0
        self.updatebuffer_lowres_width = 0
        self.updatebuffer_lowres_height = 0
        self.updatebuffer_lowres_stacknb = 0
        self.high_res_memory_names = None
        self.low_res_memory_names = None

        self.delay_cameratrigger = 0.001  # the time given for the stage to move to the new position

        self.ASLM_acquisition_time = 0.3
        self.ASLM_from_Volt = 0 #first voltage applied at remote mirror
        self.ASLM_to_Volt = 1 #voltage applied at remote mirror at the end of sawtooth
        self.ASLM_currentVolt = 0 #current voltage applied to remote mirror
        self.ASLM_staticLowResVolt = 0 #default ASLM low res voltage
        self.ASLM_staticHighResVolt = 0 #default ASLM high res voltage
        self.ASLM_alignmentOn = 0 #param=1 if ASLM alignment mode is on, otherwise zero
        self.ASLM_delaybeforevoltagereturn = 0.001 #1 ms
        self.ASLM_additionalreturntime = 0.001 # 1ms
        self.ASLM_scanWidth = ASLM_parameters.simultaneous_lines

        #preview buffers
        self.low_res_buffer = ct.SharedNDArray(shape=(Camera_parameters.LR_height_pixel, Camera_parameters.LR_width_pixel), dtype='uint16')
        self.high_res_buffer = ct.SharedNDArray(shape=(Camera_parameters.HR_height_pixel, Camera_parameters.HR_width_pixel), dtype='uint16')
        self.low_res_buffer.fill(0) #fill to initialize
        self.high_res_buffer.fill(0) #fill to initialize

        #textlabels for GUI
        self.currentFPS = str(0)

        #initialize buffers
        self.update_bufferSize()

        self.high_res_buffers_queue = queue.Queue()
        self.low_res_buffers_queue = queue.Queue()
        for i in range(2):
            self.high_res_buffers_queue.put(i)
            self.low_res_buffers_queue.put(i)

        #start initializing all hardware component here by calling the initialization from a ResultThread
        lowres_camera_init = ct.ResultThread(target=self._init_lowres_camera).start() #~3.6s
        highres_camera_init = ct.ResultThread(target=self._init_highres_camera).start() #~3.6s
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
        lowres_camera_init.get_result()
        highres_camera_init.get_result()
        filterwheel_init.get_result()
        trans_stage_init.get_result()
        rot_stage_init.get_result()
        slit_init.get_result()

        print('Finished initializing multiScope')


    def _init_lowres_camera(self):
        """
        Initialize low resolution camera
        """
        print("Initializing low resolution camera ..")
        #place the Photometrics class as object into an Object in Subprocess
        self.lowres_camera = ct.ObjectInSubprocess(Photometricscamera.Photo_Camera, 'PMPCIECam00')
        self.lowres_camera_ROI = self.lowres_camera.get_imageroi()
        print(self.lowres_camera_ROI)
        #self.lowres_camera.take_snapshot(20)
        print("done with camera.")

    def _init_highres_camera(self):
        """
        Initialize low resolution camera
        """
        print("Initializing high resolution camera..")
        #place the Photometrics class as object into an Object in Subprocess
        self.highres_camera = ct.ObjectInSubprocess(Photometricscamera.Photo_Camera, 'PMUSBCam00')
        self.highres_camera_ROI = self.highres_camera.get_imageroi()
        print(self.highres_camera_ROI)
        #self.lowres_camera.take_snapshot(20)
        print("done with camera.")

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

    def update_bufferSize(self):
        """
        This handles the size of the buffers during acquisitions.
        """

        #check for whether some image dimension parameters were changed
        if (self.updatebuffer_highres_width != self.current_highresROI_width) or (
                self.updatebuffer_highres_height != self.current_highresROI_height) or (
                self.updatebuffer_highres_stacknb != self.stack_nbplanes_highres):

            #make sure to delete previous shared memory
            if self.high_res_memory_names != None:
                print("Delete previous shared memory arrays")
                try:
                    shared_memory.SharedMemory(name=self.high_res_memory_names[0]).unlink()
                    shared_memory.SharedMemory(name=self.high_res_memory_names[1]).unlink()
                except FileNotFoundError:
                    pass  # This is the error we expected if the memory was unlinked.

            #allocate memory
            self.high_res_buffers = [ct.SharedNDArray(shape=(self.stack_nbplanes_highres, self.current_highresROI_height, self.current_highresROI_width), dtype='uint16')
                for i in range(2)]
            self.high_res_buffers[0].fill(0)
            self.high_res_buffers[1].fill(0)

            self.high_res_memory_names = [self.high_res_buffers[i].shared_memory.name for i in range(2)]
            #save current parameters so that you don't have to reallocate the memory again without image dimension changes
            self.updatebuffer_highres_width = self.current_highresROI_width
            self.updatebuffer_highres_height = self.current_highresROI_height
            self.updatebuffer_highres_stacknb = self.stack_nbplanes_highres
            print("high res buffer updated")

        if (self.updatebuffer_lowres_width != self.current_lowresROI_width) or (
                self.updatebuffer_lowres_height != self.current_lowresROI_height) or (
                self.updatebuffer_lowres_stacknb != self.stack_nbplanes_lowres):

            # make sure to delete previous shared memory
            if self.low_res_memory_names != None:
                print("Delete previous shared memory arrays")
                try:
                    shared_memory.SharedMemory(name=self.low_res_memory_names[0]).unlink()
                    shared_memory.SharedMemory(name=self.low_res_memory_names[1]).unlink()
                except FileNotFoundError:
                    pass  # This is the error we expected if the memory was unlinked.

            self.low_res_buffers = [
                ct.SharedNDArray(shape=(self.stack_nbplanes_lowres, self.current_lowresROI_height, self.current_lowresROI_width), dtype='uint16')
                for i in range(2)]

            self.low_res_buffers[0].fill(0)
            self.low_res_buffers[1].fill(0)

            self.updatebuffer_lowres_width = self.current_lowresROI_width
            self.updatebuffer_lowres_height = self.current_lowresROI_height
            self.updatebuffer_lowres_stacknb = self.stack_nbplanes_lowres
            print("low res buffer updated")
            self.low_res_memory_names = [self.high_res_buffers[i].shared_memory.name for i in range(2)]



    def close(self):
        """
        Close all opened channels, camera etc
                """
        self.finish_all_tasks()
        self.lowres_camera.close()
        self.highres_camera.close()
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
        self.move_adjustableslit(self.slitopening_highres, 1)


    def changeHRtoLR(self):
        """
        change from high resolution to low resolution acquisition settings
        """
        self.flipMirrorPosition_power.setconstantvoltage(0)
        self.move_adjustableslit(self.slitopening_lowres, 1)

    ### ---------------------------below here are the preview functions -----------------------------------------------

    def preview_lowres(self):
        """
        starts a custody thread to run a low resolution preview.
        """
        def preview_lowres_task(custody):

            self.num_frames = 0
            self.initial_time = time.perf_counter()

            def laser_preview():
                while self.continue_preview_lowres:
                    basic_unit = self.get_acq_array.get_lowres_preview_array()
                    self.ao.verbose == False
                    self.ao.play_voltages(basic_unit, block=True)


            ct.ResultThread(target=laser_preview).start()

            while self.continue_preview_lowres:
                self.lowres_camera.set_up_lowres_preview(self.exposure_time_LR)

                custody.switch_from(None, to=self.lowres_camera)
                self.lowres_camera.run_preview(out=self.low_res_buffer)

                #display
                custody.switch_from(self.lowres_camera, to=self.display)
                self.display.show_image_lowres(self.low_res_buffer)

                if self.autoscale_preview == 1:
                    minval = np.amin(self.low_res_buffer)
                    maxval = np.amax(self.low_res_buffer)
                    self.display.set_contrast(minval, maxval, "lowrespreview")
                    print("updated preview settings")

                custody.switch_from(self.display, to=None)
                self.num_frames += 1
                #calculate fps to display
                if self.num_frames == 100:
                    time_elapsed = time.perf_counter() - self.initial_time
                    print("%0.2f average FPS" % (self.num_frames / time_elapsed))
                    self.num_frames = 0
                    self.initial_time = time.perf_counter()

            self.lowres_camera.end_preview()

        self.low_res_buffer = ct.SharedNDArray(shape=(self.current_lowresROI_height, self.current_lowresROI_width), dtype='uint16')
        self.continue_preview_lowres = True
        th = ct.CustodyThread(target=preview_lowres_task, first_resource=None)
        th.start()
        return th

    ###this is the code to run a high resolution preview with a static light-sheet
    def preview_highres_static(self):
        def preview_highres_task(custody):

            self.num_frames = 0
            self.initial_time = time.perf_counter()

            def laser_preview_highres():
                #old_laserline = 0
                while self.continue_preview_highres:
                    basic_unit = self.get_acq_array.get_highres_preview_array()
                    self.ao.play_voltages(basic_unit, block=True)

            #run laser as sub-thread that is terminated when the preview button is pressed (self.continue_preview_highres is false).
            ct.ResultThread(target=laser_preview_highres).start()

            while self.continue_preview_highres:
                self.highres_camera.set_up_highrespreview(self.exposure_time_HR)
                self.num_frames += 1
                custody.switch_from(None, to=self.highres_camera)
                self.highres_camera.run_preview(out=self.high_res_buffer)

                #display acquired image
                custody.switch_from(self.highres_camera, to=self.display)
                self.display.show_image_highres(self.high_res_buffer)

                if self.autoscale_preview == 1:
                    minval = np.amin(self.high_res_buffer)
                    maxval = np.amax(self.high_res_buffer)
                    self.display.set_contrast(minval, maxval, "highrespreview")

                custody.switch_from(self.display, to=None)

                if self.num_frames == 100:
                    time_elapsed = time.perf_counter() - self.initial_time
                    avg_FPS = (self.num_frames / time_elapsed)
                    print("%0.2f average FPS" % avg_FPS)
                    self.currentFPS = str(avg_FPS)
                    self.num_frames = 0
                    self.initial_time = time.perf_counter()

            self.highres_camera.end_preview()

        self.high_res_buffer = ct.SharedNDArray(shape=(self.current_highresROI_height, self.current_highresROI_width), dtype='uint16')
        self.continue_preview_highres = True
        th = ct.CustodyThread(target=preview_highres_task, first_resource=self.highres_camera)
        th.start()
        return th

    def calculate_ASLMparameters(self, desired_exposuretime):
        """
        calculate the parameters for an ASLM acquisition
        :param desired_exposuretime: the exposure time that is desired for the whole acquisition
        :return: set the important parameters for ASLM acquisitions
        """
        linedelay = Camera_parameters.highres_line_digitization_time
        nbrows = self.current_highresROI_height
        self.ASLM_lineExposure = int(np.ceil(desired_exposuretime / (1 + nbrows/self.ASLM_scanWidth)))
        self.ASLM_line_delay = int(np.ceil((desired_exposuretime - self.ASLM_lineExposure)/(nbrows *linedelay))) - 1
        self.ASLM_acquisition_time = (self.ASLM_line_delay + 1) * nbrows * linedelay + self.ASLM_lineExposure + (self.ASLM_line_delay +1) *linedelay

        print("ASLM parameters are: {} exposure time, and {} line delay factor, {} total acquisition time for {} scan width".format(self.ASLM_lineExposure, self.ASLM_line_delay, self.ASLM_acquisition_time, self.ASLM_scanWidth))

    def preview_highres_ASLM(self):
        def preview_highresASLM_task(custody):

            self.num_frames = 0
            self.initial_time = time.perf_counter()

            while self.continue_preview_highres:

                #calculate ALSM parameters
                self.calculate_ASLMparameters(self.exposure_time_HR)
                self.highres_camera.prepare_ASLM_acquisition(self.ASLM_lineExposure, self.ASLM_line_delay)

                #generate acquisition array
                basic_unit = self.get_acq_array.get_highresASLM_preview_array()
                print("array generated")

                custody.switch_from(None, to=self.highres_camera)

                # write voltages, indicate "False" so that the voltages are not set back to zero at the end (for the remote mirror)
                write_voltages_thread = ct.ResultThread(target=self.ao._write_voltages, args=(basic_unit,False),
                                                        ).start()

                #start camera thread to poll for new images
                def start_camera_streamASLMpreview():
                    self.highres_camera.run_preview_ASLM(out=self.high_res_buffer)

                camera_stream_thread_ASLMpreview = ct.ResultThread(target=start_camera_streamASLMpreview).start()

                #play voltages
                self.ao.play_voltages(block=True, force_final_zeros=False)

                print("voltages played")
                camera_stream_thread_ASLMpreview.get_result()
                print("camera thread returned")
                self.num_frames += 1

                #display
                custody.switch_from(self.highres_camera, to=self.display)
                self.display.show_image_highres(self.high_res_buffer)

                if self.autoscale_preview == 1:
                    minval = np.amin(self.high_res_buffer)
                    maxval = np.amax(self.high_res_buffer)
                    self.display.set_contrast(minval, maxval, "highrespreview")

                custody.switch_from(self.display, to=None)


                if self.num_frames == 100:
                    time_elapsed = time.perf_counter() - self.initial_time
                    print("%0.2f average FPS" % (self.num_frames / time_elapsed))
                    self.num_frames = 0
                    self.initial_time = time.perf_counter()

            #end preview by setting voltages back to zero
            end_unit = np.zeros((100, NI_board_parameters.ao_nchannels), np.dtype(np.float64))
            self.ao.play_voltages(voltages=end_unit, block=True, force_final_zeros=False)

            self.highres_camera.end_preview()

        self.high_res_buffer = ct.SharedNDArray(shape=(self.current_highresROI_height, self.current_highresROI_width), dtype='uint16')

        #parameters for preview
        self.continue_preview_highres = True

        #start preview custody thread
        th = ct.CustodyThread(target=preview_highresASLM_task, first_resource=self.highres_camera)
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
                self.acquire_stack_lowres(current_startposition, NI_board_parameters.laser488, current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser488, current_filepath, "ASLM")
            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser488, current_filepath, "SPIM")


        if whichlaser[1]==1:
            print("acquire 552 laser")
            current_filepath = os.path.join(current_folder, "1_CH552_000000.tif")
            if resolutionmode == "low":
                self.acquire_stack_lowres(current_startposition, NI_board_parameters.laser552,
                                            current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser552, current_filepath, "ASLM")
            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser552, current_filepath, "SPIM")


        if whichlaser[2]==1:
            print("acquire 594 laser")
            current_filepath = os.path.join(current_folder, "1_CH594_000000.tif")
            if resolutionmode == "low":
                self.acquire_stack_lowres(current_startposition, NI_board_parameters.laser594,
                                            current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser594, current_filepath, "ASLM")

            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser594, current_filepath, "SPIM")

        if whichlaser[3]==1:
            print("acquire 640 laser")
            current_filepath = os.path.join(current_folder, "1_CH640_000000.tif")
            if resolutionmode == "low":
                self.acquire_stack_lowres(current_startposition, NI_board_parameters.laser640,
                                            current_filepath)
            if resolutionmode == "highASLM":
                print("acquire high res ALSM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser640, current_filepath, "ASLM")
            if resolutionmode == "highSPIM":
                print("acquire high res SPIM")
                self.acquire_stack_highres(current_startposition, NI_board_parameters.laser640, current_filepath, "SPIM")


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

        self.update_bufferSize()

        thread_stagemove.get_result()

    def acquire_stack_lowres(self, current_startposition, current_laserline, filepath):
        def acquire_task(custody):

            custody.switch_from(None, to=self.lowres_camera)

            # prepare acquisition by moving filter wheel and stage, and set buffer size
            self.prepare_acquisition(current_startposition, current_laserline)

            # prepare camera for stack acquisition - put in thread so that program executes faster :)
            def prepare_camera():
                self.lowres_camera.prepare_stack_acquisition(self.exposure_time_LR)
            camera_prepare_thread = ct.ResultThread(target=prepare_camera).start()

            #define NI board voltage array
            basic_unit = self.get_acq_array.get_lowRes_StackAq_array(current_laserline)
            control_array = np.tile(basic_unit, (self.stack_nbplanes_lowres + 1, 1))  # add +1 as you want to return to origin position

            #write voltages
            write_voltages_thread = ct.ResultThread(target=self.ao._write_voltages, args=(control_array,),
                                            ).start()

            #set up stage
            self.XYZ_stage.streamStackAcquisition_externalTrigger_setup(self.stack_nbplanes_lowres, self.lowres_planespacing, self.slow_velocity, self.slow_acceleration)

            #wait for camera set up before proceeding
            camera_prepare_thread.get_result()

            # start thread on stage to wait for trigger
            def start_stage_stream():
                self.XYZ_stage.streamStackAcquisition_externalTrigger_waitEnd()
            stream_thread = ct.ResultThread(target=start_stage_stream).start()  # ~3.6s

            def start_camera_streamfast():
                self.lowres_camera.run_stack_acquisition_buffer_fast(self.stack_nbplanes_lowres, self.low_res_buffers[current_bufferiter])
                return
            start_camera_streamfast_thread = ct.ResultThread(target=start_camera_streamfast).start()

            # play voltages - you need to use "block true" as otherwise the program finishes without playing the voltages
            self.ao.play_voltages(block=True)

            stream_thread.get_result()
            start_camera_streamfast_thread.get_result()

            custody.switch_from(self.lowres_camera, to=self.display)

            def saveimage():
                # save image
                try:
                    imwrite(filepath, self.low_res_buffers[current_bufferiter])
                except:
                    print("couldn't save image")
            savethread = ct.ResultThread(target=saveimage).start()

            if self.displayImStack ==1:
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
                all_proj = np.zeros([self.current_lowresROI_height + self.stack_nbplanes_lowres,
                                     self.current_lowresROI_width + self.stack_nbplanes_lowres])

                all_proj[0:self.current_lowresROI_height, 0:self.current_lowresROI_width] = maxproj_xy
                all_proj[self.current_lowresROI_height:, 0:self.current_lowresROI_width] = maxproj_xz
                all_proj[0:self.current_lowresROI_height, self.current_lowresROI_width:] = np.transpose(maxproj_yz)

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
            target=acquire_task, first_resource=self.lowres_camera).start()
        acquire_thread.get_result()

    def acquire_stack_highres(self, current_startposition, current_laserline, filepath, modality):
        def acquire_taskHighResSPIM(custody):
            print("start")
            custody.switch_from(None, to=self.highres_camera)

            # prepare acquisition by moving filter wheel etc
            self.prepare_acquisition(current_startposition, current_laserline)

            if modality=="ASLM":
                # obtain ASLM parameters
                self.calculate_ASLMparameters(self.exposure_time_HR)

                # define NI board voltage array
                basic_unit = self.get_acq_array.get_highResASLM_StackAq_array(current_laserline)
                control_array = np.tile(basic_unit, (
                self.stack_nbplanes_highres + 1, 1))  # add +1 as you want to return to origin position

                # smooth remote mirror voltage
                control_array[:, NI_board_parameters.voicecoil] = self.smooth_sawtooth(
                    control_array[:, NI_board_parameters.voicecoil],
                    window_len=self.ao.s2p(0.002))
                print("voltage array calculated")

                # prepare high res camera for stack acquisition
                self.highres_camera.prepare_ASLM_acquisition(self.ASLM_lineExposure, self.ASLM_line_delay)
            else:
                # define NI board voltage array
                basic_unit = self.get_acq_array.get_highResSPIM_StackAq_array(current_laserline)
                control_array = np.tile(basic_unit,
                                        (self.stack_nbplanes_highres + 1,
                                         1))  # add +1 as you want to return to origin position

                # prepare high res camera for stack acquisition
                self.highres_camera.prepare_stack_acquisition_highres(self.exposure_time_HR)
                print("camera initialized")

            # write voltages
            write_voltages_thread = ct.ResultThread(target=self.ao._write_voltages, args=(control_array,),
                                                    ).start()

            # set up stage
            self.XYZ_stage.streamStackAcquisition_externalTrigger_setup(self.stack_nbplanes_highres, self.highres_planespacing, self.slow_velocity, self.slow_acceleration)

            # start thread on stage to wait for trigger
            def start_stage_streamHighResSPIM():
                self.XYZ_stage.streamStackAcquisition_externalTrigger_waitEnd()
            stream_thread = ct.ResultThread(target=start_stage_streamHighResSPIM).start()  # ~3.6s

            def start_camera_streamHighResSPIM():
                self.highres_camera.run_stack_acquisition_buffer_fast(self.stack_nbplanes_highres,
                                                                     self.high_res_buffers[current_bufferiter])
                return

            start_highrescamera_stream_thread = ct.ResultThread(target=start_camera_streamHighResSPIM).start()


            print("stage and camera threads waiting ...")

            # play voltages
            # you need to use "block true" as otherwise the program finishes without playing the voltages really
            self.ao.play_voltages(block=True)

            stream_thread.get_result()
            start_highrescamera_stream_thread.get_result()

            custody.switch_from(self.highres_camera, to=self.display)

            def saveimage_highresSPIM():
                # save image
                try:
                    imwrite(filepath, self.high_res_buffers[current_bufferiter])
                except:
                    print("couldn't save image")
            savethread = ct.ResultThread(target=saveimage_highresSPIM).start()

            if self.displayImStack ==1:
                self.display.show_stack(self.high_res_buffers[current_bufferiter])

            def calculate_projection_highres():
                #calculate projections
                t0 = time.perf_counter()
                maxproj_xy = np.max(self.high_res_buffers[current_bufferiter], axis=0)
                maxproj_xz = np.max(self.high_res_buffers[current_bufferiter], axis=1)
                maxproj_yz = np.max(self.high_res_buffers[current_bufferiter], axis=2)
                t1 = time.perf_counter() - t0

                print("time: " + str(t1))

                ##display max projection
                all_proj = np.zeros([self.current_highresROI_height + self.stack_nbplanes_highres,
                                     self.current_highresROI_width + self.stack_nbplanes_highres])
                all_proj[0:self.current_highresROI_height, 0:self.current_highresROI_width] = maxproj_xy
                all_proj[self.current_highresROI_height:, 0:self.current_highresROI_width] = maxproj_xz
                all_proj[0:self.current_highresROI_height, self.current_highresROI_width:] = np.transpose(maxproj_yz)

                self.display.show_maxproj(all_proj)
            projection_thread2 = ct.ResultThread(target=calculate_projection_highres).start()


            custody.switch_from(self.display, to=None)
            #savethread.get_result()

        ##navigate buffer queue - where to save current image.
        current_bufferiter = self.high_res_buffers_queue.get()  # get current buffer iter
        self.high_res_buffers_queue.put(current_bufferiter)  # add number to end of queue

        #start thread and wait for its completion
        acquire_threadHighResSPIM = ct.CustodyThread(
            target=acquire_taskHighResSPIM, first_resource=self.highres_camera).start()
        acquire_threadHighResSPIM.get_result()


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
