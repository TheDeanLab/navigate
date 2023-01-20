# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


# Standard Library Imports
import sys
import logging
from tkinter import messagebox

# Third Party Imports

# Local Imports
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.view.main_window_content.acquire_bar_frame.acquire_popup import AcquirePopUp

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AcquireBarController(GUIController):
    def __init__(self, view, parent_view, parent_controller):
        super().__init__(view, parent_controller)

        self.parent_view = parent_view

        # acquisition image mode variable
        self.mode = "live"
        self.update_stack_acq(self.mode)
        self.is_save = False

        self.mode_dict = {
            "Continuous Scan": "live",
            "Z-Stack": "z-stack",
            "Single Acquisition": "single",
            "Alignment": "alignment",
            "Projection": "projection",
            "Confocal-Projection": "confocal-projection",
        }

        # gui event bind
        self.view.acquire_btn.config(command=self.launch_popup_window)
        self.view.pull_down.bind("<<ComboboxSelected>>", self.update_microscope_mode)
        self.view.exit_btn.config(command=self.exit_program)

    def progress_bar(self, images_received, microscope_state, mode, stop=False):
        """Update progress bars.

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

        Examples
        --------
        >>> progress_bar(0, microscope_state, mode)
        """

        if images_received == 0:
            if mode == "continuous":
                # Set to Indeterminate mode.
                self.view.CurAcq["mode"] = "indeterminate"
                self.view.OvrAcq["mode"] = "indeterminate"
            else:
                # Set to Determinate mode and initialize at zero.
                # stack_index = 0
                self.view.CurAcq["mode"] = "determinate"
                self.view.OvrAcq["mode"] = "determinate"
                self.view.CurAcq["value"] = 0
                self.view.OvrAcq["value"] = 0

        # Calculate the number of images anticipated.
        number_of_channels = len(
            [channel[-1] for channel in microscope_state["channels"].keys()]
        )
        number_of_timepoints = int(microscope_state["timepoints"])

        # Multiposition
        if microscope_state["is_multiposition"] is False:
            number_of_positions = 1
        else:
            number_of_positions = len(microscope_state["stage_positions"])

        if mode == "single":
            number_of_slices = 1
        elif mode == "live":
            number_of_slices = 1
        elif mode == "projection":
            number_of_slices = 1
        elif mode == "confocal-projection":
            number_of_slices = microscope_state['n_plane']
        elif mode == "z-stack":
            number_of_slices = microscope_state["number_z_steps"]

        top_anticipated_images = number_of_slices
        bottom_anticipated_images = (
            number_of_channels
            * number_of_slices
            * number_of_timepoints
            * number_of_positions
        )

        if images_received > 0:
            # Update progress bars according to imaging mode.
            if stop is False:
                if mode == "live":
                    self.view.CurAcq.start()
                    self.view.OvrAcq.start()

                elif mode == "z-stack" or "confocal-projection":
                    top_percent_complete = 100 * (
                        images_received / top_anticipated_images
                    )
                    self.view.CurAcq["value"] = top_percent_complete % 100
                    bottom_anticipated_images = 100 * (
                        images_received / bottom_anticipated_images
                    )
                    self.view.OvrAcq["value"] = bottom_anticipated_images

                elif mode == "single":
                    top_percent_complete = 100 * (
                        images_received / top_anticipated_images
                    )
                    self.view.CurAcq["value"] = top_percent_complete
                    self.view.OvrAcq["value"] = top_percent_complete

                elif mode == "projection":
                    bottom_anticipated_images = 100 * (images_received / bottom_anticipated_images)
                    self.view.CurAcq['value'] = bottom_anticipated_images
                    self.view.OvrAcq['value'] = bottom_anticipated_images

            elif stop is True:
                self.stop_progress_bar()

    def stop_progress_bar(self):
        """Stop moving the continuous progress bar."""
        self.view.CurAcq.stop()
        self.view.OvrAcq.stop()

    def set_mode(self, mode):
        """Set imaging mode.

        Parameters
        ----------
        mode: str
            Mode could be: 'live', 'z-stack', 'single', 'projection', 'confocal-projection'

        Examples
        --------
        >>> set_mode('live')
        """
        self.mode = mode
        # update pull down combobox
        reverse_dict = dict(map(lambda v: (v[1], v[0]), self.mode_dict.items()))
        self.view.pull_down.set(reverse_dict[mode])
        self.show_verbose_info("Image mode is set to", mode)

    def get_mode(self):
        """Get the current imaging mode.

        Returns
        -------
        mode : str
            Current imaging mode.

        Examples
        --------
        >>> get_mode()
        """
        return self.mode

    def stop_acquire(self):
        """Stop the acquisition.

        Examples
        --------
        >>> stop_acquire()
        """
        self.view.acquire_btn.configure(text="Acquire")

    def set_save_option(self, is_save):
        """Set whether the image will be saved.

        Parameters
        ----------
        is_save : bool
            True if we will save the data.  False if we will not.

        Examples
        --------
        >>> set_save_option(True)
        """
        self.is_save = is_save
        self.show_verbose_info("set save data option:", is_save)

    def launch_popup_window(self):
        """Launch the Save Dialog Popup Window

        The popup window should only be launched if the microscope is set to save the
        data, with the exception of the continuous acquisition mode.
        The popup window provides the user with the opportunity to fill in fields that
        describe the experiment and also dictate the save path of the data in a
        standardized format.

        Examples
        --------
        >>> launch_popup_window()
        """
        if self.view.acquire_btn["text"] == "Stop":
            # change the button to 'Acquire'
            self.view.acquire_btn.configure(text="Acquire")

            # tell the controller to stop acquire (continuous mode)
            self.parent_controller.execute("stop_acquire")

        elif self.is_save and self.mode != "live":
            acquire_pop = AcquirePopUp(self.view)
            buttons = (
                acquire_pop.get_buttons()
            )  # This holds all the buttons in the popup
            widgets = acquire_pop.get_widgets()

            # Configure the button callbacks on the popup window
            buttons["Cancel"].config(command=lambda: acquire_pop.popup.dismiss())
            buttons["Done"].config(command=lambda: self.launch_acquisition(acquire_pop))

            # Configure drop down callbacks, will update save settings when file type is
            # changed
            file_type = widgets["file_type"].get_variable()
            file_type.trace_add("write", lambda *args: self.update_file_type(file_type))

            for k, v in self.saving_settings.items():
                if widgets.get(k, None):
                    widgets[k].set(v)

        else:
            self.view.acquire_btn.configure(text="Stop")
            self.parent_controller.execute("acquire")

    def update_microscope_mode(self, *args):
        """Gets the state of the pull-down menu and tells the central controller
            Will additionally call functions to disable and enable widgets based on mode

        Parameters

        ----------
        args : str
            Imaging Mode.

        Examples
        --------
        >>> update_microscope_mode('live')
        """
        self.mode = self.mode_dict[self.view.pull_down.get()]
        self.show_verbose_info("The Microscope State is now:", self.get_mode())

        # Update state status of other widgets in the GUI based on what mode is set
        self.update_stack_acq(self.mode)
        self.update_stack_time(self.mode)
        self.update_conpro_acq(self.mode)

    def update_stack_acq(self, mode):
        """Changes state behavior of widgets in the stack acquisition frame based on
        mode of microscope

        Parameters
        ----------
        mode : str
            Imaging Mode.

        Examples
        --------
        >>> update_stack_acq('live')
        """

        # Get ref to widgets
        stack_widgets = self.parent_view.stack_acq_frame.get_widgets()

        # Grey out stack acq widgets when not Zstack or projection
        if mode == "z-stack" or mode == "projection":
            state = "normal"
        else:
            state = "disabled"
        for key, widget in stack_widgets.items():
            widget.widget["state"] = state

    def update_conpro_acq(self, mode):
        """Changes state behavior of widgets in the confocal-projection acquisition frame based on mode of microscope

        Parameters
        ----------
        mode : str
            Imaging Mode.

        Examples
        --------
        >>> update_conpro_acq('live')
        """

        # Get ref to widgets
        conpro_widgets = self.parent_view.conpro_acq_frame.get_widgets()

        # Grey out conpro acq widgets when not confocal-projection
        if mode == "confocal-projection":
            state = "normal"
        else:
            state = "disabled"
        for _, widget in conpro_widgets.items():
            widget.widget["state"] = state

    def update_stack_time(self, mode):
        """Changes state behavior of widgets in the stack timepoint frame based on mode
        of microscope

        Parameters
        ----------
        mode : str
            Imaging Mode.

        Examples
        --------
        >>> update_stack_time('live')
        """

        # Get ref to widgets
        time_widgets = self.parent_view.stack_timepoint_frame.get_widgets()

        # Grey out time widgets when in Continuous Scan or Alignment modes
        if mode == "live" or mode == "alignment":
            state = "disabled"
        else:
            state = "normal"
        for key, widget in time_widgets.items():
            widget["state"] = state

    def update_file_type(self, file_type):
        """Updates the file type when the drop down in save dialog is changed.

        Parameters
        ----------
        file_type : str
            File type.

        Examples
        --------
        >>> update_file_type('tiff')
        """
        self.saving_settings["file_type"] = file_type.get()

    def launch_acquisition(self, popup_window):
        """Launch the Acquisition.

        Once the popup window has been filled out, we first create the save path using
        the create_save_path function.
        This automatically removes spaces and replaces them with underscores.
        Then it makes the directory.
        Thereafter, the experiment is ready to go.

        Parameters
        ----------
        popup_window : object
            Instance of the popup save dialog.

        Examples
        --------
        >>> launch_acquisition(popup_window)
        """
        # update saving settings according to user's input
        self.update_experiment_values(popup_window)

        # Verify user's input is non-zero.
        is_valid = (
            self.saving_settings["user"]
            and self.saving_settings["tissue"]
            and self.saving_settings["celltype"]
            and self.saving_settings["label"]
        )

        if is_valid:
            # tell central controller, save the image/data
            self.parent_controller.execute("acquire_and_save")

            # Close the window
            popup_window.popup.dismiss()

            # We are now acquiring
            self.view.acquire_btn.configure(text="Stop")

    def exit_program(self):
        """Exit Button

        Quit the software.

        Examples
        --------
        >>> exit_program()
        """
        if messagebox.askyesno("Exit", "Are you sure?"):
            self.show_verbose_info("Exiting Program")
            # call the central controller to stop all the threads
            self.parent_controller.execute("exit")
            sys.exit()

    def populate_experiment_values(self):
        """Populate the experiment values from the config file.

        Examples
        --------
        >>> populate_experiment_values()
        """
        self.saving_settings = self.parent_controller.configuration["experiment"][
            "Saving"
        ]
        self.saving_settings["date"] = str(self.saving_settings["date"])
        mode = self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "image_mode"
        ]
        self.set_mode(mode)

    def update_experiment_values(self, popup_window):
        """Gets the entries from the popup save dialog and overwrites the
        saving_settings dictionary.

        Parameters
        ----------
        popup_window : object
            Instance of the popup save dialog.

        Examples
        --------
        >>> update_experiment_values(popup_window)
        """
        popup_vals = popup_window.get_variables()
        for name in popup_vals:
            # remove leading and tailing whitespaces
            self.saving_settings[name] = popup_vals[name].strip()
