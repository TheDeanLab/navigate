from controller.sub_controllers.gui_controller import GUI_Controller


class Camera_Setting_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # Getting Widgets/Buttons
        self.mode_widgets = view.camera_mode.get_widgets() # keys = ['Sensor', 'Readout', 'Dual', 'Split']
        self.framerate_widgets = view.framerate_info.get_widgets() # keys = ['Temp1', 'Temp2', 'Temp3', 'Exposure', 'Integration']
        self.roi_widgets = view.camera_roi.get_widgets() # roi_keys = ['Left', 'Right', 'Top', 'Bottom'], fov_keys = ['FOV_X', 'FOV_Y'], center_keys = ['Center_X', 'Center_Y'], num_pix_keys = ['Pixels_X', 'Pixels_Y']
        self.roi_btns = view.camera_roi.get_buttons() # keys = ['Center_ROI', 'Center_At', 'Use_Pixels', '1024', '512'] 


        # Setting Preset options for widgets
        self.sensor_values = ['Normal', 'Light Sheet']
        self.mode_widgets['Sensor'].set_values(self.sensor_values)
        self.mode_widgets['Sensor'].set('Normal')