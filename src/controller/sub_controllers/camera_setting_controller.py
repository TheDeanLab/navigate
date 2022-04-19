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
        # keys = ['Sensor', 'Readout', 'Pixels']
        self.mode_widgets = view.camera_mode.get_widgets()
        self.framerate_widgets = view.framerate_info.get_widgets()
        # keys = ['Temp1', 'Temp2', 'Temp3', 'Exposure', 'Integration']

        self.roi_widgets = view.camera_roi.get_widgets()
        # roi_keys = ['Left', 'Right', 'Top', 'Bottom'], fov_keys =
        # ['FOV_X', 'FOV_Y'], center_keys = ['Center_X', 'Center_Y'], num_pix_keys = ['Pixels_X', 'Pixels_Y']

        self.roi_btns = view.camera_roi.get_buttons()
        # keys = ['Center_ROI', 'Center_At', 'Use_Pixels', '1024', '512']

        self.sensor_mode = self.parent_controller.configuration.CameraParameters[
            'sensor_mode']
        self.readout_direction = self.parent_controller.configuration.CameraParameters[
            'sensor_mode']
        self.pixel_size = self.parent_controller.configuration.CameraParameters[
            'pixel_size_in_microns']
        self.width = self.parent_controller.configuration.CameraParameters['x_pixels']
        self.height = self.parent_controller.configuration.CameraParameters['y_pixels']

        # Binding for Camera Mode
        self.mode_widgets['Sensor'].widget.bind(
            '<<ComboboxSelected>>', self.update_readout)

        # Binding for Readout Mode
        self.mode_widgets['Readout'].widget.bind(
            '<<ComboboxSelected>>', self.action_readout)
        # TODO: Make abstraction for cameras.  Need a function to call in
        # Hamamatsu.

        # Binding for ROI Mode
        # Trace examples
        # self.roi_widgets['Right'].widget.config(command=self.update_pixels, relief="sunken") # TODO change button style during transitions
        #self.roi_widgets['Right'].widget.trace('w', command=self.update_pixels)
        #self.roi_widgets['Right'].widget.bind('<<ComboboxSelected>>', self.action_readout)

        # self.roi_widgets['Left'].widget.config(command=self.update_pixels)
        # self.roi_widgets['Top'].widget.config(command=self.update_pixels)
        # self.roi_widgets['Bottom'].widget.config(command=self.update_pixels)

        self.initialize(configuration_controller)

    def initialize(self, config):
        '''
        #### Function that sets widgets based on data given from main controller/config
        '''
        # Camera Mode
        self.mode_widgets['Sensor'].widget['values'] = [
            'Normal', 'Light Sheet']
        self.mode_widgets['Sensor'].widget['state'] = 'readonly'
        self.mode_widgets['Sensor'].widget.selection_clear()
        self.mode_widgets['Pixels'].widget['state'] = 'disabled'

        self.mode_widgets['Readout'].widget['values'] = [
            ' ', 'Top to Bottom', 'Bottom to Top']
        self.mode_widgets['Readout'].widget['state'] = 'disabled'
        self.mode_widgets['Readout'].selection_clear()

        # set range value
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

    def set_experiment_values(self, setting_dict):
        # Number of Cameras.
        # ... set(setting_dict['number_of_cameras'])

        # Readout Settings
        self.mode_widgets['Sensor'].set(setting_dict['sensor_mode'])
        self.mode_widgets['Readout'].set(setting_dict['readout_direction'])

        # FOV Settings
        # self.mode_widgets['Width'].set(setting_dict['x_pixels'])
        # self.mode_widgets['Height'].set(setting_dict['y_pixels'])

        # Binning Settings
        # ... set(setting_dict['binning'])

        # populate pixels {
        #   'low': self.configuration.ZoomParameters['high_res_zoom_pixel_size'],
        #   'high': self.configuration.ZoomParameters['low_res_zoom_pixel_size']
        # }

        # Populating FOV Mode
        # TODO: Not sure why zoom is being populated as low.  Cannot currently
        # track down. Hardcoded.

        # ROI Mode: 'pixels'
        # width = setting_dict['width']
        # height = setting_dict['height']
        # top = 1
        # left = 1

        # ROI Center
        # self.roi_widgets['Center_X'].set(width/2)
        # self.roi_widgets['Center_Y'].set(height/2)

        # Framerate
        # TODO Kevin this is where the widgets have their default values set, uncomment what you want set initially
        # self.framerate_widgets['Temp1'].set(data[0])
        # self.framerate_widgets['Temp2'].set(data[1])
        # self.framerate_widgets['Temp3'].set(data[2])
        # self.framerate_widgets['Exposure'].set(data[3])
        # self.framerate_widgets['Integration'].set(data[4])

        # FOV
        # pixel_size = setting_dict['pixel_size']
        # zoom = setting_dict['zoom']
        # #TODO: Adjust to account for zoom changes.
        # self.roi_widgets['FOV_X'].set(self.pixel_size)
        # self.roi_widgets['FOV_Y'].set(self.pixel_size)

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

    def update_readout(self, *args):
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

    def action_readout(self, *args):
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
