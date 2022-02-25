from controller.sub_controllers.gui_controller import GUI_Controller


class Camera_Setting_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # Getting Widgets/Buttons
        self.mode_widgets = view.camera_mode.get_widgets() # keys = ['Sensor', 'Readout', 'Dual', 'Split']
        self.framerate_widgets = view.framerate_info.get_widgets() # keys = ['Temp1', 'Temp2', 'Temp3', 'Exposure', 'Integration']
        self.roi_widgets = view.camera_roi.get_widgets() # roi_keys = ['Left', 'Right', 'Top', 'Bottom'], fov_keys = ['FOV_X', 'FOV_Y'], center_keys = ['Center_X', 'Center_Y'], num_pix_keys = ['Pixels_X', 'Pixels_Y']
        self.roi_btns = view.camera_roi.get_buttons() # keys = ['Center_ROI', 'Center_At', 'Use_Pixels', '1024', '512'] 

        # Binding
        self.mode_widgets['Sensor'].widget.bind('<<ComboboxSelected>>', self.update_readout)
        self.mode_widgets['Readout'].widget.bind('<<ComboboxSelected>>', self.action_readout)


    def initialize(self, name, data):
        '''
        #### Function that sets widgest based on data given from main controller/config
        '''
        if name == 'sensor mode':
            self.mode_widgets['Sensor'].widget['values'] = data
            self.mode_widgets['Sensor'].widget.set('Normal')
            self.mode_widgets['Sensor'].widget['state'] = 'readonly'
            self.mode_widgets['Sensor'].widget.selection_clear()

        if name == 'readout':
            self.mode_widgets['Readout'].widget['values'] = data
            self.mode_widgets['Readout'].widget.set(' ')
            self.mode_widgets['Readout'].widget['state'] = 'readonly'
            self.mode_widgets['Readout'].selection_clear()
    
     
    def update_readout(self, *args):
        '''
        #### Updates text in readout widget based on what sensor mode is selected
        '''
        sensor_value = self.mode_widgets['Sensor'].widget.get()
        if sensor_value == 'Normal':
            self.mode_widgets['Readout'].widget.set(' ')
            self.mode_widgets['Readout'].widget['state'] = 'disabled'
            self.mode_widgets['Sensor'].widget.selection_clear()
        if sensor_value == 'Light Sheet':
            self.mode_widgets['Readout'].widget.set('Top to Bottom')
            self.mode_widgets['Readout'].widget['state'] = 'readonly'

    def action_readout(self, *args):
        '''
        #### Logic for controlling what backend data needs changing based on readout setting
        '''
        pass
    