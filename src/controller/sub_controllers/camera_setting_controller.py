"""
ASLM sub-controller for the camera settings.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from controller.sub_controllers.gui_controller import GUI_Controller


class Camera_Setting_Controller(GUI_Controller):
    def __init__(
            self,
            view,
            parent_controller=None,
            verbose=False,
            configuration_controller=None):
        super().__init__(view, parent_controller, verbose)

        # default values
        self.in_initialization = True
        self.resolution_value = '1x'
        
        # Getting Widgets/Buttons
        self.mode_widgets = view.camera_mode.get_widgets()
        self.framerate_widgets = view.framerate_info.get_widgets()
        self.roi_widgets = view.camera_roi.get_widgets()
        self.roi_btns = view.camera_roi.get_buttons()

        # initialize
        self.initialize(configuration_controller)

        # Event binding
        self.mode_widgets['Sensor'].widget.bind('<<ComboboxSelected>>', self.update_sensor_mode)
        self.framerate_widgets['exposure_time'].get_variable().trace_add('write', self.update_exposure_time)
        self.roi_widgets['Width'].get_variable().trace_add('write', self.update_fov)
        self.roi_widgets['Height'].get_variable().trace_add('write', self.update_fov)
        self.mode_widgets['Pixels'].get_variable().trace_add('write', self.update_fov)
        
        for btn_name in self.roi_btns:
            self.roi_btns[btn_name].config(
                command=self.update_roi(btn_name)
            )

    def initialize(self, config):
        '''
        ## Function that sets widgets based on data given from main controller/config
        '''

        # Get Default Configuration Values
        self.default_pixel_size = config.configuration.CameraParameters['pixel_size_in_microns']
        self.default_width, self.default_height = config.get_pixels()
        self.trigger_source = config.configuration.CameraParameters['trigger_source']
        self.trigger_active = config.configuration.CameraParameters['trigger_active']
        
        # Camera Mode
        self.mode_widgets['Sensor'].widget['values'] = ['Normal', 'Light-Sheet']
        self.mode_widgets['Sensor'].widget['state'] = 'readonly'
        self.mode_widgets['Sensor'].widget.set(config.configuration.CameraParameters['sensor_mode'])
        self.mode_widgets['Sensor'].widget.selection_clear()

        # Readout Mode
        self.mode_widgets['Readout'].widget['values'] = [' ', 'Top-to-Bottom', 'Bottom-to-Top']
        self.mode_widgets['Readout'].widget['state'] = 'disabled'
        self.mode_widgets['Readout'].selection_clear()

        # Pixels
        self.mode_widgets['Pixels'].widget['state'] = 'disabled'
        self.mode_widgets['Pixels'].set(self.default_pixel_size)
        self.mode_widgets['Pixels'].widget.config(from_=1) # min value
        self.mode_widgets['Pixels'].widget.config(to=config.configuration.CameraParameters['y_pixels'] / 2) # max value
        self.mode_widgets['Pixels'].widget.config(increment=1) # step value

        # framerate_widgets
        self.framerate_widgets['exposure_time'].widget.min = config.configuration.CameraParameters['exposure_time_range']['min']
        self.framerate_widgets['exposure_time'].widget.max = config.configuration.CameraParameters['exposure_time_range']['max']
        self.framerate_widgets['exposure_time'].set(config.configuration.CameraParameters['exposure_time'])
        self.framerate_widgets['exposure_time'].widget['state'] = 'normal'

        # Set range value
        self.roi_widgets['Width'].widget.config(to=self.default_width)
        self.roi_widgets['Width'].widget.config(from_=2)
        self.roi_widgets['Width'].widget.config(increment=2)
        self.roi_widgets['Height'].widget.config(to=self.default_height)
        self.roi_widgets['Height'].widget.config(from_=2)
        self.roi_widgets['Height'].widget.config(increment=2)

        # Center position
        self.roi_widgets['Center_X'].set(self.default_width/2)
        self.roi_widgets['Center_Y'].set(self.default_height/2)

        # This should not be edited for now
        # Center position
        self.roi_widgets['Center_X'].widget['state'] = 'disabled'
        self.roi_widgets['Center_Y'].widget['state'] = 'disabled'
        # FOV
        self.roi_widgets['FOV_X'].widget['state'] = 'disabled'
        self.roi_widgets['FOV_Y'].widget['state'] = 'disabled'

    def set_experiment_values(self, experiment):
        """
        Experiment yaml filed passed by controller.
        """
        self.in_initialization = True

        setting_dict = experiment.CameraParameters
        microscope_state = experiment.MicroscopeState
        self.resolution_value = 'high' if microscope_state['resolution_mode'] == 'high' else microscope_state['zoom']

        # Readout Settings
        self.mode_widgets['Sensor'].set(setting_dict['sensor_mode'])
        self.mode_widgets['Readout'].set(setting_dict['readout_direction'])

        # FOV Settings
        self.roi_widgets['Width'].set(setting_dict['x_pixels'])
        self.roi_widgets['Height'].set(setting_dict['y_pixels'])

        # Camera Framerate Info - 'exposure_time', 'readout_time', 'framerate', 'frames_to_average'
        # Currently for just the first channel
        exposure_time = microscope_state['channels']['channel_1']['camera_exposure_time']
        self.framerate_widgets['exposure_time'].set(exposure_time)

        # TODO: Currently the frame rate and the readout time is calculated in the model.camera class.
        # readout_time, max_frame_rate = self.parent_controller.model.camera.calculate_readout_time()
        # self.framerate_widgets['readout_time'].set(readout_time)
        # self.framerate_widgets['framerate'].set(max_frame_rate)

        # Binning
        self.framerate_widgets['frames_to_average'].set(setting_dict['frames_to_average'])

        # Physical Dimensions
        self.calculate_physical_dimensions(self.resolution_value)
        # readout time
        self.calculate_readout_time()
        
        # after initialization
        self.in_initialization = False


    def update_experiment_values(self, setting_dict):
        """
        Update the dictionary so that it can be combined with all of the other
        sub-controllers, and then sent to the model.
        """
        # Camera Operation Mode
        setting_dict['sensor_mode'] = self.mode_widgets['Sensor'].get()
        if setting_dict['sensor_mode'] == 'Light-Sheet':
            setting_dict['readout_direction'] = self.mode_widgets['Readout'].get()

        # Camera Binning
        setting_dict['binning'] = 1

        # Camera FOV Size.
        setting_dict['x_pixels'] = self.roi_widgets['Width'].get()
        setting_dict['y_pixels'] = self.roi_widgets['Height'].get()

        setting_dict['number_of_cameras'] = 1
        setting_dict['pixel_size'] = self.mode_widgets['Pixels'].get()
        setting_dict['frames_to_average'] = self.framerate_widgets['frames_to_average'].get()

        return True

    def update_sensor_mode(self, *args):
        '''
        Updates text in readout widget based on what sensor mode is selected
        If we are in the Light Sheet mode, then we want the camera
        self.model.CameraParameters['sensor_mode']) == 12

        If we are in the normal mode, then we want the camera
        self.model.CameraParameters['sensor_mode']) == 1

        Should initialize from the configuration file to the default version
        '''
        # Camera Mode
        sensor_value = self.mode_widgets['Sensor'].widget.get()
        if sensor_value == 'Normal':
            self.mode_widgets['Readout'].set(' ')
            self.mode_widgets['Readout'].widget['state'] = 'disabled'
            self.mode_widgets['Pixels'].widget['state'] = 'disabled'
            self.mode_widgets['Pixels'].widget.set(self.default_pixel_size)
            self.mode_widgets['Sensor'].widget.selection_clear()
            
            self.show_verbose_info("Normal Camera Readout Mode")

        if sensor_value == 'Light-Sheet':
            self.mode_widgets['Readout'].widget.set('Top to Bottom')
            self.mode_widgets['Readout'].widget['state'] = 'readonly'
            self.mode_widgets['Pixels'].set(10)  # Default to 10 pixels
            self.mode_widgets['Pixels'].widget['state'] = 'normal'
            
            self.show_verbose_info("Light Sheet Camera Readout Mode")
        
        # calculate readout time
        self.calculate_readout_time()

    def update_exposure_time(self, *args):
        """
        # when camera exposure time is changed, recalculate readout time
        # tell central controller
        """
        self.calculate_readout_time()

        # TODO: tell central controller to update channel
        
        self.show_verbose_info('Camera exposure time is changed to', self.framerate_widgets['exposure_time'].get())

    def update_roi(self, width):
        """
        # update roi width and height
        """
        width = self.default_width if width=='All' else float(width)
        def handler(*args):
            self.roi_widgets['Width'].set(width)
            self.roi_widgets['Height'].set(width)
            self.show_verbose_info("ROI width and height are changed to", width, width)
        return handler

    def update_fov(self, *args):
        """
        # recalculate fov and update the widgets: FOV_X and FOV_Y
        """
        if self.in_initialization:
            return
        self.calculate_physical_dimensions(self.resolution_value)

    def set_mode(self, mode):
        """
        # this function will change state of widgets according to different mode
        # 'stop' mode will let the editable widget be 'normal'
        # in 'live' and 'stack' mode, some widgets are disabled
        # TODO: make sure all the widgets act right as more experiment modes are supported.
        """
        state = 'normal' if mode == 'stop' else 'disabled'
        self.mode_widgets['Sensor'].widget['state'] = state
        if self.mode_widgets['Sensor'].get() == 'Light-Sheet':
            self.mode_widgets['Readout'].widget['state'] = state
        self.framerate_widgets['exposure_time'].widget['state'] = state
        self.framerate_widgets['frames_to_average'].widget['state'] = state
        self.roi_widgets['Width'].widget['state'] = state
        self.roi_widgets['Height'].widget['state'] = state
        for btn_name in self.roi_btns:
            self.roi_btns[btn_name]['state'] = state
        
    def calculate_physical_dimensions(self, resolution_value):
        """
        Calculates the size of the field of view according to the magnification of the system,
        the physical size of the pixel, and the number of pixels.
        update FOV_X and FOV_Y
        """
        if resolution_value == 'high':
            tube_lens_focal_length = 300
            multi_immersion_focal_length = 8.4
            magnification = tube_lens_focal_length / multi_immersion_focal_length
        else:
            magnification = resolution_value
            magnification = float(magnification[:-1])

        pixel_size = float(self.mode_widgets['Pixels'].widget.get())
        x_pixel = float(self.roi_widgets['Width'].get())
        y_pixel = float(self.roi_widgets['Height'].get())

        physical_dimensions_x = x_pixel * pixel_size / magnification
        physical_dimensions_y = y_pixel * pixel_size / magnification

        self.roi_widgets['FOV_X'].set(physical_dimensions_x)
        self.roi_widgets['FOV_Y'].set(physical_dimensions_y)
    
    def calculate_readout_time(self):
        """
        # Calculates it here, what if we change to a new camera?
        """
        h = 9.74436 * 10 ** -6  # Readout timing constant
        # the ROI height 'subarray_vsize'
        vn = float(self.roi_widgets['Height'].get())
        sensor_mode = self.mode_widgets['Sensor'].get()
        exposure_time = float(self.framerate_widgets['exposure_time'].get())

        if sensor_mode == 'Normal':
            #  Area sensor mode operation
            if self.trigger_source == 1:
                # Internal Trigger Source
                max_frame_rate = 1 / ((vn/2)*h)
                readout_time = exposure_time - ((vn/2)*h)

            if self.trigger_active in [1, 2]:
                #  External Trigger Source
                #  Edge == 1, Level == 2
                max_frame_rate = 1 / ((vn/2) * h + exposure_time + 10*h)
                readout_time = exposure_time - ((vn/2) * h + exposure_time + 10*h)

            elif self.trigger_active == 3:
                #  External Trigger Source
                #  Synchronous Readout == 3
                max_frame_rate = 1 / ((vn/2) * h + 5*h)
                readout_time = exposure_time - ((vn/2) * h + 5*h)

        elif sensor_mode == 'Light-Sheet':
            #  Progressive sensor mode operation
            max_frame_rate = 1 / (exposure_time + (vn+10)*h)
            readout_time = exposure_time - 1 / (exposure_time + (vn+10)*h)

        # return readout_time, max_frame_rate
        self.framerate_widgets['readout_time'].set(readout_time)
        self.framerate_widgets['max_framerate'].set(max_frame_rate)
