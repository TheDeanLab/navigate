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
        self.widgets = self.view.get_widgets()
        self.mode_widget = self.widgets['Mode']
        self.mag_widget = self.widgets['Mag']

        self.variables = self.view.get_variables()
        self.lasers = ['488nm', '562nm', '642nm']
        self.mode = None
        self.mag = None
        self.other_info_dict = {
            'Delay': 'delay_percent',
            'Duty': '',
            'Smoothing': ''
        }

        # add validations to widgets
        for laser in self.lasers:
            validate_wrapper(self.widgets[laser + ' Amp'].widget, is_entry=True)
            validate_wrapper(self.widgets[laser + ' Off'].widget, is_entry=True)
        for key in self.other_info_dict.keys():
            validate_wrapper(self.widgets[key].widget, is_entry=True)

        
        # event combination
        self.mode_widget.widget.bind('<<ComboboxSelected>>', self.show_magnification)
        self.mag_widget.widget.bind('<<ComboboxSelected>>', self.show_laser_info)

        for laser in self.lasers:
            self.variables[laser + ' Amp'].trace_add('write', self.update_etl_setting(laser+' Amp', laser, 'amplitude'))
            self.variables[laser + ' Off'].trace_add('write', self.update_etl_setting(laser+' Off', laser, 'offset'))

        self.variables['Delay'].trace_add('write', self.update_other_setting('Delay'))

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

    def show_magnification(self, *args):
        """
        # show magnification options when the user changes the focus mode
        """
        # get mode setting
        self.mode = self.mode_widget.widget.get()
        temp = list(self.resolution_info.ETLConstants[self.mode].keys())
        self.mag_widget.widget['values'] = temp
        self.mag_widget.widget.set(temp[0])
        # update laser info
        self.show_laser_info()
        self.show_other_info(self.mode)

    def show_laser_info(self, *args):
        """
        # show laser info when the user changes magnification setting
        """
        # get magnification setting
        self.mag = self.mag_widget.widget.get()
        for laser in self.lasers:
            self.variables[laser + ' Amp'].set(self.resolution_info.ETLConstants[self.mode][self.mag][laser]['amplitude'])
            self.variables[laser + ' Off'].set(self.resolution_info.ETLConstants[self.mode][self.mag][laser]['offset'])
        
    def show_other_info(self, mode):
        """
        # show delay_percent, pulse_percent.
        """
        if mode == 'low':
            prefix = 'remote_focus_l_'
        else:
            prefix = 'remote_focus_r_'
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

    def update_other_setting(self, name):
        """
        # this function will update Delay, Duty, and Smoothing setting when something is changed
        """
        variable = self.variables[name]
        info_name = self.other_info_dict[name]
        
        def func(*args):
            if self.mode == 'low':
                prefix = 'remote_focus_l_'
            else:
                prefix = 'remote_focus_r_'

            self.other_info[prefix + info_name] = variable.get()
        return func

    
    def save_etl_info(self):
        """
        # this function will save etl to new yaml file.
        """
        errors = self.get_errors()
        if errors:
            return # Dont save if any errors TODO needs testing
        filename = filedialog.asksaveasfilename(defaultextension='.yml', filetypes=[('Yaml file', '*.yml')])
        if not filename:
            return
        save_yaml_file('', self.resolution_info.serialize(), filename)

    '''
        Example for preventing submission of a field/controller. So if there is an error in any field that is supposed to have validation then the config cannot be saved
    '''
    # TODO needs testing may also need to be moved to the remote_focus_popup class. Opinions welcome
    def get_errors(self):
        '''Get a list of field errors in popup'''

        errors = {}
        for key, labelInput in self.widgets.items():
            if hasattr(labelInput.widget,'trigger_focusout_validation'):
                labelInput.widget.trigger_focusout_validation()
            if labelInput.error.get():
                errors[key] = labelInput.error.get()
        return errors
