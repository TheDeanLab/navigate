from tkinter import filedialog

from controller.sub_controllers.widget_functions import validate_wrapper
from controller.sub_controllers.gui_controller import GUI_Controller
from controller.aslm_controller_functions import save_yaml_file

class Etl_Popup_Controller(GUI_Controller):

    def __init__(self, view, parent_controller, verbose=False):
        super().__init__(view, parent_controller, verbose)

        self.resolution_info = None
        self.other_info = None
        # get mode and mag widgets
        widgets = self.view.get_widgets()
        self.mode_widget = widgets['Mode']
        self.mag_widget = widgets['Mag']

        self.variables = self.view.get_variables()
        self.lasers = ['488nm', '562nm', '642nm']
        self.mode = None
        self.mag = None

        # add validations to widgets
        for laser in self.lasers:
            validate_wrapper(widgets[laser + ' Amp'].widget, is_entry=True)
            validate_wrapper(widgets[laser + ' Off'].widget, is_entry=True)

        # event combination
        self.mode_widget.widget.bind('<<ComboboxSelected>>', self.update_magnification)
        self.mag_widget.widget.bind('<<ComboboxSelected>>', self.update_laser)

        for laser in self.lasers:
            self.variables[laser + ' Amp'].trace_add('write', self.update_etl_setting(laser+' Amp', laser, 'amplitude'))
            self.variables[laser + ' Off'].trace_add('write', self.update_etl_setting(laser+' Off', laser, 'offset'))

        self.view.get_buttons()['Save'].configure(command=self.save_etl_info)

    def initialize(self, name, data):
        """
        # initialize widgets with data
        """
        if name == 'resolution':
            self.resolution_info = data
            self.mode_widget.widget['values'] = list(data.ETLConstants.keys())
        else:
            self.other_info = data

    def update_magnification(self, *args):
        """
        # update magnification options when the user changes the focus mode
        """
        # get mode setting
        self.mode = self.mode_widget.widget.get()
        temp = list(self.resolution_info.ETLConstants[self.mode].keys())
        self.mag_widget.widget['values'] = temp
        self.mag_widget.widget.set(temp[0])
        # update laser info
        self.update_laser()
        self.update_other_info(self.mode)

    def update_laser(self, *args):
        """
        # update laser info when the user changes magnification setting
        """
        # get magnification setting
        self.mag = self.mag_widget.widget.get()
        for laser in self.lasers:
            self.variables[laser + ' Amp'].set(self.resolution_info.ETLConstants[self.mode][self.mag][laser]['amplitude'])
            self.variables[laser + ' Off'].set(self.resolution_info.ETLConstants[self.mode][self.mag][laser]['offset'])
        
    def update_other_info(self, mode):
        """
        # update delay_percent, pulse_percent.
        """
        if mode == 'low':
            prefix = 'laser_l_'
        else:
            prefix = 'laser_r_'
        self.variables['Delay'].set(self.other_info[prefix+'delay_percent'])
        self.variables['Smoothing'].set(self.other_info[prefix+'pulse_percent'])

    def update_etl_setting(self, name, laser, etl_name):
        """
        # this function will update ETLConstains in memory
        """
        variable = self.variables[name]

        def func_laser(*args):
            self.resolution_info.ETLConstants[self.mode][self.mag][laser][etl_name] = variable.get()

        return func_laser
    
    def save_etl_info(self):
        """
        # this function will save etl to new yaml file.
        """
        filename = filedialog.asksaveasfilename(defaultextension='.yml', filetypes=[('Yaml file', '*.yml')])
        if not filename:
            return
        save_yaml_file('', self.resolution_info.serialize(), filename)
