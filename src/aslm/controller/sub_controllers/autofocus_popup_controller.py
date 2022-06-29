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
from aslm.controller.sub_controllers.gui_controller import GUI_Controller
from aslm.controller.aslm_controller_functions import combine_funcs
import time

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Autofocus_Popup_Controller(GUI_Controller):

    def __init__(self, view, parent_controller, verbose=False, setting_dict=None):
        super().__init__(view, parent_controller, verbose)

        self.widgets = self.view.get_widgets()
        self.setting_dict = setting_dict
        self.autofocus_fig = self.view.fig
        self.autofocus_coarse = self.view.coarse
        self.autofocus_fine = self.view.fine


        # show the value
        for k in self.widgets:
            self.widgets[k].set(setting_dict[k])
        self.view.stage_vars[0].set(setting_dict['coarse_selected'])
        self.view.stage_vars[1].set(setting_dict['fine_selected'])

        # add saving function to the function closing the window
        exit_func = combine_funcs(self.update_experiment_values, self.view.popup.dismiss,
                                    lambda: delattr(self.parent_controller, 'af_popup_controller'))
        self.view.popup.protocol("WM_DELETE_WINDOW", exit_func)

        self.view.autofocus_btn.configure(command=self.start_autofocus)

    def update_experiment_values(self, setting_dict=None):
        if not setting_dict:
            setting_dict = self.setting_dict
        for k in self.widgets:
            setting_dict[k] = self.widgets[k].get()
        setting_dict['coarse_selected'] = self.view.stage_vars[0].get()
        setting_dict['fine_selected'] = self.view.stage_vars[1].get()

    def showup(self):
        """
        # this function will let the popup window show in front
        """
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)

    def start_autofocus(self):
        self.update_experiment_values()
        # self.view.popup.dismiss()
        # delattr(self.parent_controller,'af_popup_controller')
        self.parent_controller.execute('autofocus')
        
    def display_plot(self, data):
        '''
        ### Displays a plot of [focus, entropy] with data from autofocus routine
        '''
    
        coarse_range = self.setting_dict['coarse_range']
        coarse_step = self.setting_dict['coarse_step_size']


        # Calculate the coarse portion of the data
        coarse_steps = int(coarse_range) // int(coarse_step) + 1

        
        # Plotting coarse data
        self.autofocus_coarse.clear()
        self.autofocus_coarse.plot(data[:coarse_steps, 0], data[:coarse_steps, 1], 'bo')

        # Plotting fine data
        self.autofocus_fine.clear()
        self.autofocus_fine.plot(data[coarse_steps:, 0], data[coarse_steps:, 1], 'g*')
        
        # To redraw the plot
        self.autofocus_fig.canvas.draw_idle()
        
        