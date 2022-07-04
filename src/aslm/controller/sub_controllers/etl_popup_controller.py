"""
ASLM sub-controller ETL popup window.

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
from tkinter import filedialog

from aslm.controller.sub_controllers.gui_controller import GUI_Controller
from aslm.controller.aslm_controller_functions import save_yaml_file, combine_funcs

import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


# TODO: Should we rename to remote_focus_popup_controller?
class Etl_Popup_Controller(GUI_Controller):
    def __init__(self, view, parent_controller, remote_focus_dict, etl_file_name, configuration_dict, galvo_dict,
                 verbose=False):
        """
        Controller for remote focus parameters.

        Parameters
        ----------
        view : object
            GUI element containing widgets and variables to control. Likely tk.Toplevel-derived.
        parent_controller : ASLM_controller
            The main controller.
        remote_focus_dict : dict
            Dictionary of remote focus device parameters for each zoom/wavelength.
        etl_file_name : str
            Location of file where remote_focus_dict is read from/saved to.
        configuration_dict : dict
            Dictionary containing microscope hardware configuration, such as voltage limits for remote focus hardware.
        galvo_dict : dict
            Dictionary containing galvo frequency, amplitude, offset. From the experiment dictionary.
        verbose : bool, default False
            Display additional feedback in standard output.

        Returns
        -------
        None
        """
        super().__init__(view, parent_controller, verbose)

        self.resolution_info = remote_focus_dict
        self.configuration = configuration_dict
        self.galvo_setting = galvo_dict
        self.etl_file_name = etl_file_name
        # get mode and mag widgets
        self.widgets = self.view.get_widgets()

        self.variables = self.view.get_variables()

        self.lasers = [v for k, v in self.configuration.LaserParameters.items() if k.endswith('wavelength')]
        self.resolution = None
        self.mag = None
        self.in_initialize = True
        self.mode = 'stop'

        # event id list
        self.event_ids = {}
        for mode in self.resolution_info.ETLConstants:
            for mag in self.resolution_info.ETLConstants[mode]:
                self.event_ids[mode+'_'+mag] = None

        # event combination
        self.widgets['Mode'].widget.bind('<<ComboboxSelected>>', self.show_magnification)
        self.widgets['Mag'].widget.bind('<<ComboboxSelected>>', self.show_laser_info)

        for laser in self.lasers:
            self.variables[laser + ' Amp'].trace_add('write', self.update_etl_setting(laser+' Amp', laser, 'amplitude'))
            self.variables[laser + ' Off'].trace_add('write', self.update_etl_setting(laser+' Off', laser, 'offset'))

        self.variables['Galvo Amp'].trace_add('write', self.update_galvo_setting('Galvo Amp', 'amplitude'))
        self.variables['Galvo Off'].trace_add('write', self.update_galvo_setting('Galvo Off', 'offset'))
        self.variables['Galvo Freq'].trace_add('write', self.update_galvo_setting('Galvo Freq', 'frequency'))

        self.view.get_buttons()['Save'].configure(command=self.save_etl_info)

        # add saving function to the function closing the window
        self.view.popup.protocol("WM_DELETE_WINDOW",
                                 combine_funcs(self.save_etl_info, self.view.popup.dismiss,
                                               lambda: delattr(self.parent_controller, 'etl_controller')))

        # Populate widgets
        self.widgets['Mode'].widget['values'] = list(self.resolution_info.ETLConstants.keys())
        print(self.widgets['Mode'].widget['values'])
        self.widgets['Mode'].widget['state'] = 'readonly'
        self.widgets['Mag'].widget['state'] = 'readonly'

        self.configure_widget_range()

    def configure_widget_range(self):
        """
        Update the widget ranges and precisions based on the current resolution mode.
        """

        if self.resolution == 'high':
            precision = -3
            increment = 0.001
            focus_prefix = 'r'
        else:
            # resolution is low
            precision = -2
            increment = 0.01
            focus_prefix = 'l'

        laser_min = self.configuration.RemoteFocusParameters[f'remote_focus_{focus_prefix}_min_ao']
        laser_max = self.configuration.RemoteFocusParameters[f'remote_focus_{focus_prefix}_max_ao']
        galvo_min = self.configuration.GalvoParameters[f'galvo_{focus_prefix}_min_ao']
        galvo_max = self.configuration.GalvoParameters[f'galvo_{focus_prefix}_max_ao']

        # set ranges of value for those lasers
        for laser in self.lasers:
            self.widgets[laser + ' Amp'].widget.configure(from_=laser_min)
            self.widgets[laser + ' Amp'].widget.configure(to=laser_max)
            self.widgets[laser + ' Amp'].widget.configure(increment=increment)
            self.widgets[laser + ' Amp'].widget.set_precision(precision)
            # TODO: The offset bounds should adjust based on the amplitude bounds,
            #       so that amp + offset does not exceed the bounds. Can be done
            #       in update_etl_setting()
            self.widgets[laser + ' Off'].widget.configure(from_=laser_min)
            self.widgets[laser + ' Off'].widget.configure(to=laser_max)
            self.widgets[laser + ' Off'].widget.configure(increment=increment)
            self.widgets[laser + ' Off'].widget.set_precision(precision)

        self.widgets['Galvo Amp'].widget.configure(from_=galvo_min)
        self.widgets['Galvo Amp'].widget.configure(to=galvo_max)
        self.widgets['Galvo Amp'].widget.configure(increment=increment)
        self.widgets['Galvo Amp'].widget.set_precision(precision)
        # TODO: The offset bounds should adjust based on the amplitude bounds,
        #       so that amp + offset does not exceed the bounds. Can be done
        #       in update_etl_setting()
        self.widgets['Galvo Off'].widget.configure(from_=galvo_min)
        self.widgets['Galvo Off'].widget.configure(to=galvo_max)
        self.widgets['Galvo Off'].widget.configure(increment=increment)
        self.widgets['Galvo Off'].widget.set_precision(precision)

        self.widgets['Galvo Freq'].widget.configure(from_=0)
        self.widgets['Galvo Freq'].widget.configure(increment=increment)
        self.widgets['Galvo Freq'].widget.set_precision(precision)

        # The galvo by default uses a sawtooth waveform. However, sometimes we have a resonant galvo.
        # In the case of the resonant galvo, the amplitude must be zero and only the offset can be
        # controlled. We only define the offset in the configuration.yml file. If only the offset is
        # defined for galvo_{focus_prefix}, we disable the amplitude.
        #
        # TODO: Are there other parameters we wish to enable/disable based on configuration?
        # TODO: Should we instead change galvo amp/offset behavior based on a waveform type passed in the
        #       configuration? That is, should we pass galvo_l_waveform: sawtooth and galvo_r_waveform: dc_value?
        #       And then adjust the ETL_Popup_Controller accordingly? We could do the same for ETL vs. voice coil.
        if self.configuration.GalvoParameters.get(f'galvo_{focus_prefix}_amplitude', None) is None:
            self.widgets['Galvo Amp'].widget['state'] = "disabled"
            self.widgets['Galvo Freq'].widget['state'] = "disabled"
        else:
            self.widgets['Galvo Amp'].widget['state'] = "normal"
            self.widgets['Galvo Freq'].widget['state'] = "normal"

    def set_experiment_values(self, resolution_value):
        """
        # set experiment values
        """
        self.in_initialize = True
        self.widgets['Mode'].set('high' if resolution_value == 'high' else 'low')
        self.show_magnification()
        self.widgets['Mag'].set('N/A' if resolution_value == 'high' else resolution_value)
        self.show_laser_info()
        
        # end initialization
        self.in_initialize = False

    def set_mode(self, mode='stop'):
        self.mode = mode

    def showup(self):
        """
        # this function will let the popup window show in front
        """
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)

    def show_magnification(self, *args):
        """
        # show magnification options when the user changes the focus mode
        """
        # get resolution setting
        self.resolution = self.widgets['Mode'].widget.get()
        temp = list(self.resolution_info.ETLConstants[self.resolution].keys())
        self.widgets['Mag'].widget['values'] = temp
        self.widgets['Mag'].widget.set(temp[0])
        # update laser info
        self.show_laser_info()

    def show_laser_info(self, *args):
        """
        # show laser info when the user changes magnification setting
        """
        # get magnification setting
        self.mag = self.widgets['Mag'].widget.get()
        for laser in self.lasers:
            self.variables[laser + ' Amp'].set(self.resolution_info.ETLConstants
                                               [self.resolution][self.mag][laser]['amplitude'])
            self.variables[laser + ' Off'].set(self.resolution_info.ETLConstants
                                               [self.resolution][self.mag][laser]['offset'])

        focus_prefix = 'r' if self.resolution == 'high' else 'l'

        self.variables['Galvo Amp'].set(self.galvo_setting.get(f'galvo_{focus_prefix}_amplitude', 0))
        self.variables['Galvo Off'].set(self.galvo_setting.get(f'galvo_{focus_prefix}_offset', 0))
        self.variables['Galvo Freq'].set(self.galvo_setting.get(f'galvo_{focus_prefix}_frequency', 0))

        if not self.in_initialize:
            # update resolution value in central controller (menu)
            self.parent_controller.resolution_value.set('high' if self.resolution == 'high' else self.mag)
            # reconfigure widgets
            self.configure_widget_range()

    def update_etl_setting(self, name, laser, etl_name):
        r"""This function will update ETLConstants in memory
        """
        variable = self.variables[name]

        def func(temp):
            self.parent_controller.execute('update_setting', 'resolution', temp)

        # TODO: Is this still a bug?
        # BUG Upon startup this will always run 0.63x, and when changing magnification it will run 0.63x
        # before whatever mag is selected
        def func_laser(*args):
            value = self.resolution_info.ETLConstants[self.resolution][self.mag][laser][etl_name]

            # Will only run code if value in constants does not match whats in GUI for Amp or Off AND in Live mode
            # TODO: Make also work in the 'single' acquisition mode.
            variable_value = variable.get()
            print("ETL Amplitude/Offset Changed: ", variable_value)
            if value != variable_value and variable_value != '':  # and self.mode == 'live':
                self.resolution_info.ETLConstants[self.resolution][self.mag][laser][etl_name] = variable_value
                if self.verbose:
                    print("ETL Amplitude/Offset Changed: ", variable_value)
                logger.debug(f"ETL Amplitude/Offset Changed:, {variable_value}")
                # tell parent controller (the device)
                event_id_name = self.resolution + '_' + self.mag
                if self.event_ids[event_id_name]:
                    self.view.popup.after_cancel(self.event_ids[event_id_name])
                temp = {
                    'resolution_mode': self.resolution,
                    'zoom': self.mag,
                    'laser_info': self.resolution_info.ETLConstants[self.resolution][self.mag]
                }

                # Delay feature.
                self.event_ids[event_id_name] = self.view.popup.after(500, lambda: func(temp))

        return func_laser

    def update_galvo_setting(self, name, parameter):
        variable = self.variables[name]

        def func(temp):
            self.parent_controller.execute('update_setting', 'galvo', temp)

        def func_galvo(*args):
            focus_prefix = 'r' if self.resolution == 'high' else 'l'
            galvo_parameter = f'galvo_{focus_prefix}_{parameter}'
            value = self.galvo_setting[galvo_parameter]
            variable_value = variable.get()
            print(f"Galvo parameter {galvo_parameter} changed: {variable_value}")
            if value != variable_value and variable_value != '':  # and self.mode == 'live':
                self.galvo_setting[galvo_parameter] = variable.get()
                if self.verbose:
                    print(f"Galvo parameter {galvo_parameter} changed: {variable_value}")
                logger.debug(f"Galvo parameter {galvo_parameter} changed: {variable_value}")
                event_id_name = galvo_parameter
                try:
                    if self.event_ids[event_id_name]:
                        self.view.popup.after_cancel(self.event_ids[event_id_name])
                except KeyError:
                    pass

                temp = {galvo_parameter: float(variable_value)}
                self.event_ids[event_id_name] = self.view.popup.after(500, lambda: func(temp))

        return func_galvo
    
    def save_etl_info(self):
        """
        This function will save updated remote focus parameters to their yaml file.

        TODO: This currently does not save the galvo parameters, even though they are controlled here.
              Right now, these must be saved in the experiment file separately.
        """
        errors = self.get_errors()
        if errors:
            return  # Dont save if any errors TODO needs testing

        save_yaml_file('', self.resolution_info.serialize(), self.etl_file_name)

    """
    Example for preventing submission of a field/controller. So if there is an error in any field that 
    is supposed to have validation then the config cannot be saved.
    """
    # TODO needs testing may also need to be moved to the remote_focus_popup class. Opinions welcome
    def get_errors(self):
        """
        Get a list of field errors in popup
        """

        errors = {}
        for key, labelInput in self.widgets.items():
            if hasattr(labelInput.widget, 'trigger_focusout_validation'):
                labelInput.widget.trigger_focusout_validation()
            if labelInput.error.get():
                errors[key] = labelInput.error.get()
        return errors
