from controller.sub_controllers.gui_controller import GUI_Controller


class Camera_Setting_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # Getting Widgets/Buttons
        self.mode_widgets = view.camera_mode.get_widgets() # keys = ['Sensor', 'Readout', 'Pixels']
        self.framerate_widgets = view.framerate_info.get_widgets() # keys = ['Temp1', 'Temp2', 'Temp3', 'Exposure', 'Integration']
        self.roi_widgets = view.camera_roi.get_widgets() # roi_keys = ['Left', 'Right', 'Top', 'Bottom'], fov_keys = ['FOV_X', 'FOV_Y'], center_keys = ['Center_X', 'Center_Y'], num_pix_keys = ['Pixels_X', 'Pixels_Y']
        self.roi_btns = view.camera_roi.get_buttons() # keys = ['Center_ROI', 'Center_At', 'Use_Pixels', '1024', '512'] 

        # Binding for Camera Mode
        self.mode_widgets['Sensor'].widget.bind('<<ComboboxSelected>>', self.update_readout)
        self.mode_widgets['Readout'].widget.bind('<<ComboboxSelected>>', self.action_readout)

        # Binding for ROI Mode
        self.roi_widgets['Right'].widget.config(command=self.update_pixels)
        self.roi_widgets['Left'].widget.config(command=self.update_pixels)
        self.roi_widgets['Top'].widget.config(command=self.update_pixels)
        self.roi_widgets['Bottom'].widget.config(command=self.update_pixels)


    def initialize(self, name, data):
        '''
        #### Function that sets widgest based on data given from main controller/config
        '''
        # Camera Mode
        if name == 'sensor mode':
            self.mode_widgets['Sensor'].widget['values'] = data
            self.mode_widgets['Sensor'].set('Normal')
            self.mode_widgets['Sensor'].widget['state'] = 'readonly'
            self.mode_widgets['Sensor'].widget.selection_clear()
            self.mode_widgets['Pixels'].widget['state'] = 'disabled'

        if name == 'readout':
            self.mode_widgets['Readout'].widget['values'] = data
            self.mode_widgets['Readout'].set(' ')
            self.mode_widgets['Readout'].widget['state'] = 'disabled'
            self.mode_widgets['Readout'].selection_clear()

        # Framerate
        if name == 'framerate':
            # TODO Kevin this is where the widgets have their default values set, uncomment what you want set initially
            # self.framerate_widgets['Temp1'].set(data[0])
            # self.framerate_widgets['Temp2'].set(data[1])
            # self.framerate_widgets['Temp3'].set(data[2])
            # self.framerate_widgets['Exposure'].set(data[3])
            # self.framerate_widgets['Integration'].set(data[4])
            pass

        # Roi Mode
        if name == 'pixels':
            right = data[0]
            bottom = data[1]
            top = 1
            left = 1
            # Setting default roi widgets
            self.roi_widgets['Right'].set(right) # Image width aka X pixels
            self.roi_widgets['Bottom'].set(bottom) # Imgage height aka Y pixels
            self.roi_widgets['Left'].set(left) # Base value of 1 pixel to start
            self.roi_widgets['Top'].set(top) # Same as above
            # Setting num of pixels
            self.roi_widgets['Pixels_X'].set(right - left - 1)
            self.roi_widgets['Pixels_Y'].set(bottom - top - 1)
            self.roi_widgets['Pixels_X'].widget['state'] = 'disabled' # This should not be edited for now
            self.roi_widgets['Pixels_Y'].widget['state'] = 'disabled'
            # ROI Center
            self.roi_widgets['Center_X'].set(right/2)
            self.roi_widgets['Center_Y'].set(bottom/2)
            self.roi_widgets['Center_X'].widget['state'] = 'disabled' # This should not be edited for now
            self.roi_widgets['Center_Y'].widget['state'] = 'disabled'

        # FOV
        if name == 'fov':
            mode = data[0]
            pixel_size = data[1]
            self.roi_widgets['FOV_X'].set(pixel_size)
            self.roi_widgets['FOV_Y'].set(pixel_size)
            self.roi_widgets['FOV_X'].widget['state'] = 'disabled'
            self.roi_widgets['FOV_Y'].widget['state'] = 'disabled'

        
    def update_readout(self, *args):
        '''
        #### Updates text in readout widget based on what sensor mode is selected
        '''
        # Camera Mode
        sensor_value = self.mode_widgets['Sensor'].widget.get()
        if sensor_value == 'Normal':
            self.mode_widgets['Readout'].set(' ')
            self.mode_widgets['Readout'].widget['state'] = 'disabled'
            self.mode_widgets['Pixels'].widget['state'] = 'disabled'
            self.mode_widgets['Sensor'].widget.selection_clear()
        if sensor_value == 'Light Sheet':
            self.mode_widgets['Readout'].widget.set('Top to Bottom')
            self.mode_widgets['Readout'].widget['state'] = 'readonly'
            self.mode_widgets['Pixels'].set(10) # Default to 10 pixels
            self.mode_widgets['Pixels'].widget['state'] = 'normal'

    def action_readout(self, *args):
        '''
        #### Logic for controlling what backend data needs changing based on readout setting
        '''
        pass

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
    