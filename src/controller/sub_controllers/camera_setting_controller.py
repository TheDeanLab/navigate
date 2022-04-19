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

        # Getting Widgets/Buttons
        self.mode_widgets = view.camera_mode.get_widgets()
        self.framerate_widgets = view.framerate_info.get_widgets()
        self.roi_widgets = view.camera_roi.get_widgets()
        self.roi_btns = view.camera_roi.get_buttons()

        # Get Default Configuration Values
        self.sensor_mode = self.parent_controller.configuration.CameraParameters['sensor_mode']
        self.readout_direction = self.parent_controller.configuration.CameraParameters['sensor_mode']
        self.pixel_size = self.parent_controller.configuration.CameraParameters['pixel_size_in_microns']
        self.width = self.parent_controller.configuration.CameraParameters['x_pixels']
        self.height = self.parent_controller.configuration.CameraParameters['y_pixels']

        # Binding for Camera Mode
        self.mode_widgets['Sensor'].widget.bind('<<ComboboxSelected>>', self.update_sensor_mode)

        # Binding for Readout Mode
        self.mode_widgets['Readout'].widget.bind('<<ComboboxSelected>>', self.update_readout_direction)

        # Binding for ROI Mode
        # Trace examples
        # self.roi_widgets['Right'].widget.config(command=self.update_pixels, relief="sunken") # TODO change button style during transitions
        #self.roi_widgets['Right'].widget.trace('w', command=self.update_pixels)
        #self.roi_widgets['Right'].widget.bind('<<ComboboxSelected>>', self.update_readout_direction)

        # self.roi_widgets['Left'].widget.config(command=self.update_pixels)
        # self.roi_widgets['Top'].widget.config(command=self.update_pixels)
        # self.roi_widgets['Bottom'].widget.config(command=self.update_pixels)

        self.initialize(configuration_controller)

    def initialize(self, config):
        '''
        ## Function that sets widgets based on data given from main controller/config
        '''
        # Camera Mode
        self.mode_widgets['Sensor'].widget['values'] = ['Normal', 'Light-Sheet']
        self.mode_widgets['Sensor'].widget['state'] = 'readonly'
        self.mode_widgets['Sensor'].widget.selection_clear()
        self.mode_widgets['Pixels'].widget['state'] = 'disabled'

        # Readout Mode
        self.mode_widgets['Readout'].widget['values'] = [' ', 'Top-to-Bottom', 'Bottom-to-Top']
        self.mode_widgets['Readout'].widget['state'] = 'disabled'
        self.mode_widgets['Readout'].selection_clear()

        # Set range value
        width, height = config.get_pixels(self.verbose)
        self.roi_widgets['Width'].widget.config(to=width)
        self.roi_widgets['Height'].widget.config(to=height)

        # This should not be edited for now
        self.roi_widgets['Center_X'].widget['state'] = 'disabled'
        self.roi_widgets['Center_Y'].widget['state'] = 'disabled'

        # This should not be edited for now
        self.roi_widgets['Center_X'].widget['state'] = 'disabled'
        self.roi_widgets['Center_Y'].widget['state'] = 'disabled'

        # FOV
        self.roi_widgets['FOV_X'].widget['state'] = 'disabled'
        self.roi_widgets['FOV_Y'].widget['state'] = 'disabled'

    def calculate_physical_dimensions(self, setting_dict):
        """
        Calculates the size of the field of view according to the magnification of the system,
        the physical size of the pixel, and the number of pixels.
        """
        if self.parent_controller.experiment.MicroscopeState['resolution_mode'] == 'high':
            tube_lens_focal_length = 300
            multi_immersion_focal_length = 8.4
            magnification = tube_lens_focal_length / multi_immersion_focal_length
        else:
            magnification = self.parent_controller.experiment.MicroscopeState['zoom']
            magnification = float(magnification[:-1])

        physical_dimensions_x = setting_dict['x_pixels'] * self.pixel_size / magnification
        physical_dimensions_y = setting_dict['y_pixels'] * self.pixel_size / magnification
        return [physical_dimensions_x, physical_dimensions_y]


    def set_experiment_values(self, experiment):
        """
        Experiment yaml filed passed by controller.
        """
        setting_dict = experiment.CameraParameters
        microscope_state = experiment.MicroscopeState

        # Readout Settings
        self.mode_widgets['Sensor'].set(setting_dict['sensor_mode'])
        self.mode_widgets['Readout'].set(setting_dict['readout_direction'])

        # FOV Settings
        self.roi_widgets['Center_X'].set(setting_dict['x_pixels'] / 2)
        self.roi_widgets['Center_Y'].set(setting_dict['y_pixels'] / 2)
        self.roi_widgets['Width'].set(setting_dict['x_pixels'])
        self.roi_widgets['Height'].set(setting_dict['y_pixels'])

        # Physical Dimensions
        [physical_dimensions_x, physical_dimensions_y] = self.calculate_physical_dimensions(setting_dict)
        self.roi_widgets['FOV_X'].set(physical_dimensions_x)
        self.roi_widgets['FOV_Y'].set(physical_dimensions_y)

        # Camera Framerate Info - 'exposure_time', 'readout_time', 'framerate', 'images_to_average'
        # Currently for just the first channel
        exposure_time = microscope_state['channels']['channel_1']['camera_exposure_time']
        self.framerate_widgets['exposure_time'].set(exposure_time)

        # TODO: Currently the frame rate and the readout time is calculated in the model.camera class.
        # readout_time, max_frame_rate = self.parent_controller.model.camera.calculate_readout_time()
        # self.framerate_widgets['readout_time'].set(readout_time)
        # self.framerate_widgets['framerate'].set(max_frame_rate)

        # Binning
        self.framerate_widgets['images_to_average'].set(setting_dict['frames_to_average'])


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
        setting_dict['pixel_size'] = self.roi_widgets['FOV_X'].get()

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
            self.mode_widgets['Sensor'].widget.selection_clear()
            self.sensor_mode = 'Normal'
            if self.verbose:
                print("Normal Camera Readout Mode")

        if sensor_value == 'Light-Sheet':
            self.mode_widgets['Readout'].widget.set('Top to Bottom')
            self.mode_widgets['Readout'].widget['state'] = 'readonly'
            self.mode_widgets['Pixels'].set(10)  # Default to 10 pixels
            self.mode_widgets['Pixels'].widget['state'] = 'normal'
            self.sensor_mode = 'Light-Sheet'
            if self.verbose:
                print("Light Sheet Camera Readout Mode")

    def update_readout_direction(self, *args):
        '''
        #### Trace function when changes to the readout direction are made.
        '''
        self.readout_direction = self.mode_widgets['Readout'].widget.get()
        if self.verbose:
            print("Readout Direction:", self.readout_direction)

    def update_pixels(self, *args):
        '''
        #### Updates number of pixels in ROI based on Right, Left, Top, Bottom
        '''

        right = self.roi_widgets['Right'].get()
        left = self.roi_widgets['Left'].get()
        top = self.roi_widgets['Top'].get()
        bottom = self.roi_widgets['Bottom'].get()

        self.roi_widgets['Pixels_X'].set(right - left - 1)
        self.roi_widgets['Pixels_Y'].set(bottom - top - 1)
