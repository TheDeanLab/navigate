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
from aslm.controller.sub_controllers.gui_controller import GUI_Controller
from aslm.view.main_window_content.acquire_bar_frame.acquire_popup import Acquire_PopUp as acquire_popup

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[1]
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
            'label': '',
            'file_type': ''
        }

        self.mode_dict = { 
            'Continuous Scan': 'live',
            'Z-Stack': 'z-stack',
            'Single Acquisition': 'single',
            'Projection': 'projection'
        }  #need to add alignment here

        # gui event bind
        self.view.acquire_btn.config(command=self.launch_popup_window)
        self.view.pull_down.bind('<<ComboboxSelected>>',self.update_microscope_mode)
        self.view.exit_btn.config(command=self.exit_program)
        self.parent_view = parent_view

    def progress_bar(self,
                     images_received,
                     microscope_state,
                     mode,
                     stop=False):
        r"""Update progress bars.

        Parameters
        ----------
        microscope_state : dict
            State of the microscope.  Positions, channels, z-steps, etc.
        mode : str
            Imaging mode.  'live', 'z-stack', ...
        images_received : int
            Number of images received in the controller.
        stop : bool
            Stop flag to set back to 0.
        """

        if images_received == 0:
            if mode == 'continuous':
                # Set to Indeterminate mode.
                self.view.CurAcq['mode'] = 'indeterminate'
                self.view.OvrAcq['mode'] = 'indeterminate'
            else:
                # Set to Determinate mode and initialize at zero.
                stack_index = 0
                self.view.CurAcq['mode'] = 'determinate'
                self.view.OvrAcq['mode'] = 'determinate'
                self.view.CurAcq['value'] = 0
                self.view.OvrAcq['value'] = 0

        # Calculate the number of images anticipated.
        number_of_channels = len([channel[-1] for channel in microscope_state['channels'].keys()])
        number_of_timepoints = int(microscope_state['timepoints'])

        # Multiposition
        if microscope_state['is_multiposition'] == False:
             number_of_positions = 1
        else:
            number_of_positions = len(microscope_state['stage_positions'])

        if mode == 'single':
            number_of_slices = 1
        elif mode == 'live':
            number_of_slices = 1
        elif mode == 'projection':
            number_of_slices = 1
        elif mode == 'z-stack':
            number_of_slices = microscope_state['number_z_steps']

        top_anticipated_images = number_of_slices
        bottom_anticipated_images = number_of_channels * \
                                    number_of_slices * \
                                    number_of_timepoints * \
                                    number_of_positions

        if images_received > 0:
            # Update progress bars according to imaging mode.
            if stop is False:
                if mode == 'live':
                    self.view.CurAcq.start()
                    self.view.OvrAcq.start()

                elif mode == 'z-stack':
                    top_percent_complete = 100 * (images_received / top_anticipated_images)
                    self.view.CurAcq['value'] = top_percent_complete % 100
                    bottom_anticipated_images = 100 * (images_received / bottom_anticipated_images)
                    self.view.OvrAcq['value'] = bottom_anticipated_images

                elif mode == 'single':
                    top_percent_complete = 100 * (images_received / top_anticipated_images)
                    self.view.CurAcq['value'] = top_percent_complete
                    self.view.OvrAcq['value'] = top_percent_complete

                elif mode == 'projection':
                    pass

            elif stop is True:
                self.stop_progress_bar()

    def stop_progress_bar(self):
        r"""Stop moving the continuous progress bar."""
        self.view.CurAcq.stop()
        self.view.OvrAcq.stop()

    def set_mode(self,
                 mode):
        r"""Set imaging mode.

        Parameters
        ----------
        mode: str
            Mode could be: 'live', 'z-stack', 'single', 'projection'
        """
        self.mode = mode
        # update pull down combobox
        reverse_dict = dict(map(lambda v: (v[1], v[0]), self.mode_dict.items()))
        self.view.pull_down.set(reverse_dict[mode])
        self.show_verbose_info('image mode is set to', mode)

    def get_mode(self):
        r"""Get the current imaging mode.

        Returns
        -------
        mode : str
            Current imaging mode.
        """
        return self.mode

    def stop_acquire(self):
        r"""Stop the acquisition."""
        self.view.acquire_btn.configure(text='Acquire')

    def set_save_option(self,
                        is_save):
        r"""Set whether the image will be saved.

        Parameters
        ----------
        is_save : bool
            True if we will save the data.  False if we will not.
        """
        self.is_save = is_save
        self.show_verbose_info('set save data option:', is_save)

    def set_saving_settings(self,
                            saving_settings):
        r"""Set saving settings

        Parameters
        ----------
        saving_settings : dict
            Dictionary with root_directory, save_directory, user, etc. Reference to configuration.experiment.Saving.
        """
        # if value is None, set to ''
        for name in saving_settings:
            if saving_settings[name] is None:
                saving_settings[name] = ''
        self.saving_settings = saving_settings
        self.show_verbose_info('Set saving settings')

    def launch_popup_window(self):
        r"""Launches the Save Dialog Popup Window

        The popup window should only be launched if the microscope is set to save the data,
        with the exception of the continuous acquisition mode.
        The popup window provides the user with the opportunity to fill in fields that describe the experiment and
        also dictate the save path of the data in a standardized format.
        """
        if self.view.acquire_btn['text'] == 'Stop':
            # change the button to 'Acquire'
            self.view.acquire_btn.configure(text='Acquire')

            # tell the controller to stop acquire (continuous mode)
            self.parent_controller.execute('stop_acquire')

        elif self.is_save and self.mode != 'live':
            acquire_pop = acquire_popup(self.view)
            buttons = acquire_pop.get_buttons()  # This holds all the buttons in the popup
            widgets = acquire_pop.get_widgets()

            # Configure the button callbacks on the popup window
            buttons['Cancel'].config(command=lambda: acquire_pop.popup.dismiss(self.verbose))
            buttons['Done'].config(command=lambda: self.launch_acquisition(acquire_pop))

            # Configure drop down callbacks, will update save settings when file type is changed
            file_type = widgets['file_type'].get_variable()
            file_type.trace_add('write', lambda *args: self.update_file_type(file_type))

            initialize_popup_window(acquire_pop, self.saving_settings)

        else:
            self.view.acquire_btn.configure(text='Stop')
            self.parent_controller.execute('acquire')

    def update_microscope_mode(self,
                               *args):
        r"""Gets the state of the pull-down menu and tells the central controller

        Parameters
        ----------
        args : str
            Imaging Mode.
        """
        self.mode = self.mode_dict[self.view.pull_down.get()]
        if self.mode in ["live", "Alignment"]: # need to get alignment
            self.parent_view.stack_timepoint_frame.save_check['state'] = "disabled"
            self.parent_view.stack_timepoint_frame.exp_time_spinbox['state'] = "disabled"
            self.parent_view.stack_timepoint_frame.stack_acq_spinbox['state'] = "disabled"
            self.parent_view.stack_timepoint_frame.stack_pause_spinbox['state'] = "disabled"
            self.parent_view.stack_timepoint_frame.timepoint_interval_spinbox['state'] = "disabled"
            self.parent_view.stack_timepoint_frame.total_time_spinval['state'] = "disabled"
        self.show_verbose_info("The Microscope State is now:", self.get_mode())

    def update_file_type(self,
                         file_type):
        r"""Updates the file type when the drop down in save dialog is changed.

        Parameters
        ----------
        file_type : str
            File type.
        """
        self.saving_settings['file_type'] = file_type.get()

    def launch_acquisition(self,
                           popup_window):
        r"""Launch the Acquisition.

        Once the popup window has been filled out, we first create the save path using the create_save_path function.
        This automatically removes spaces and replaces them with underscores.
        Then it makes the directory.
        Thereafter, the experiment is ready to go.

        Parameters
        ----------
        popup_window : object
            Instance of the popup save dialog.
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

            # We are now acquiring
            self.view.acquire_btn.configure(text='Stop')

    def exit_program(self):
        r"""Exit Button

        Quits the software.
        """
        self.show_verbose_info("Exiting Program")
        # call the central controller to stop all the threads
        self.parent_controller.execute('exit')
        sys.exit()

    def update_saving_settings(self, popup_window):
        r"""Gets the entries from the popup save dialog and overwrites the saving_settings dictionary."""
        popup_vals = popup_window.get_variables()
        for name in popup_vals:
            # remove leading and tailing whitespaces
            self.saving_settings[name] = popup_vals[name].strip()


def initialize_popup_window(popup_window,
                            values):
    """This function initializes the popup window

    Parameters
    ----------
    popup_window : object
        Instance of the popup save dialog.
    values : dict
        {'root_directory':, 'save_directory':, 'user':, 'tissue':,'celltype':,'label':, 'file_type':}
    """
    popup_vals = popup_window.get_widgets()
    for name in values:
        if popup_vals.get(name, None):
            popup_vals[name].set(values[name])
