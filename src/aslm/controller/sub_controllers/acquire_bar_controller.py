"""
ASLM sub-controller for the acquire popup window.
When the mode is changed, we need to communicate this to the central controller.
Central controller then communicates these changes to the channel_setting_controller.

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
import sys
from controller.sub_controllers.gui_controller import GUI_Controller
from view.main_window_content.acquire_bar_frame.acquire_popup import Acquire_PopUp as acquire_popup

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

class Acquire_Bar_Controller(GUI_Controller):
    def __init__(self, view, parent_view, parent_controller, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # acquisition image mode variable
        self.mode = 'live'
        self.is_save = False
        self.saving_settings = {
            'root_directory': 'E:\\',
            'save_directory': '',
            'user': '',
            'tissue': '',
            'celltype': '',
            'label': ''
        }

        self.mode_dict = {
            'Continuous Scan': 'live',
            'Z-Stack': 'z-stack',
            'Single Acquisition': 'single',
            'Projection': 'projection'
        }

        # gui event bind
        self.view.acquire_btn.config(command=self.launch_popup_window)

        self.view.pull_down.bind(
            '<<ComboboxSelected>>',
            self.update_microscope_mode)

        self.view.exit_btn.config(command=self.exit_program)
        
        self.parent_view = parent_view

    def set_mode(self, mode):
        """
        # set image mode
        # mode could be: 'live', 'z-stack', 'single', 'projection'
        """
        self.mode = mode
        # update pull down combobox
        reverse_dict = dict(
            map(lambda v: (v[1], v[0]), self.mode_dict.items()))
        self.view.pull_down.set(reverse_dict[mode])

        self.show_verbose_info('image mode is set to', mode)

    def get_mode(self):
        """
        # return right now image mode setting
        """
        return self.mode

    def stop_acquire(self):
        self.view.acquire_btn.configure(text='Acquire')

    def set_save_option(self, is_save):
        """
        # set whether the image will be saved
        """
        self.is_save = is_save

        self.show_verbose_info('set save data option:', is_save)

    def set_saving_settings(self, saving_settings):
        """
        # set saving settings
        # right now it is a reference to the model.exprement.Saving
        """
        # if value is None, set to ''
        for name in saving_settings:
            if saving_settings[name] is None:
                saving_settings[name] = ''

        self.saving_settings = saving_settings

        self.show_verbose_info('set saving settings')

    def launch_popup_window(self):
        """
        # The popup window should only be launched if the microscope is set to save the data,
        # with the exception of the continuous acquisition mode.
        # The popup window provides the user with the opportunity to fill in fields that describe the experiment and
        # also dictate the save path of the data in a standardized format.
        """
        if self.is_save and self.mode != 'live':
            acquire_pop = acquire_popup(self.view)
            buttons = acquire_pop.get_buttons()  # This holds all the buttons in the popup

            # Configure the button callbacks on the popup window
            buttons['Cancel'].config(
                command=lambda: acquire_pop.popup.dismiss(
                    self.verbose))
            buttons['Done'].config(
                command=lambda: self.launch_acquisition(acquire_pop))

            initialize_popup_window(acquire_pop, self.saving_settings)

        elif self.view.acquire_btn['text'] == 'Stop':
            # change the button to 'Acquire'
            self.view.acquire_btn.configure(text='Acquire')

            # tell the controller to stop acquire(continuous mode)
            self.parent_controller.execute('stop_acquire')
        else:
            # if the mode is 'live'
            if self.mode == 'live':
                self.view.acquire_btn.configure(text='Stop')
            self.parent_controller.execute('acquire')

    def update_microscope_mode(self, *args):
        """
        # Gets the state of the pull-down menu and tell the central controller
        """
        self.mode = self.mode_dict[self.view.pull_down.get()]
        if self.mode not in ["z-stack", "projection"]: 
            self.parent_view.stack_acq_frame.step_size_spinbox['state'] = "disabled"
            self.parent_view.stack_acq_frame.start_pos_spinbox['state'] = "disabled"
            self.parent_view.stack_acq_frame.end_pos_spinbox['state'] = "disabled"
            self.parent_view.stack_acq_frame.slice_spinbox['state'] = "disabled"
        else:
            self.parent_view.stack_acq_frame.step_size_spinbox['state'] = "normal"
            self.parent_view.stack_acq_frame.start_pos_spinbox['state'] = "normal"
            self.parent_view.stack_acq_frame.end_pos_spinbox['state'] = "normal"
            self.parent_view.stack_acq_frame.slice_spinbox['state'] = "normal"
        self.show_verbose_info("The Microscope State is now:", self.get_mode())

    def launch_acquisition(self, popup_window):
        """
        # Once the popup window has been filled out, we first create the save path using the create_save_path function.
        # This automatically removes spaces and replaces them with underscores.
        # Then it makes the directory.
        # Thereafter, the experiment is ready to go.
        """
        # update saving settings according to user's input
        self.update_saving_settings(popup_window)

        # Verify user's input is non-zero.
        is_valid = self.saving_settings['user'] and self.saving_settings['tissue'] \
            and self.saving_settings['celltype'] and self.saving_settings['label']

        if is_valid:
            # tell central controller, save the image/data
            self.parent_controller.execute(
                'acquire_and_save', self.saving_settings)

            # Close the window
            popup_window.popup.dismiss(self.verbose)

    def exit_program(self):
        self.show_verbose_info("Exiting Program")
        # call the central controller to stop all the threads
        self.parent_controller.execute('exit')
        sys.exit()

    def update_saving_settings(self, popup_window):
        popup_vals = popup_window.get_variables()
        for name in popup_vals:
            # remove leading and tailing whitespaces
            self.saving_settings[name] = popup_vals[name].strip()


def initialize_popup_window(popup_window, values):
    """
    # this function will initialize popup window
    # values should be a dict {
    #    'root_directory':,
    #    'save_directory':,
    #    'user':,
    #    'tissue':,
    #    'celltype':,
    #    'label':
    # }
    """
    popup_vals = popup_window.get_widgets()

    for name in values:
        if popup_vals.get(name, None):
            popup_vals[name].set(values[name])
