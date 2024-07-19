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
import logging
from tkinter import messagebox

# Third Party Imports

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.view.popups.acquire_popup import AcquirePopUp

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AcquireBarController(GUIController):
    """Acquire Bar Controller."""

    def __init__(self, view, parent_controller):
        """Initialize the Acquire Bar Controller.

        Parameters
        ----------
        view : object
            Instance of the View.
        parent_controller : object
            Instance of the Main Controller.
        """
        super().__init__(view, parent_controller)

        #: str: Acquisition image mode.
        self.mode = "live"

        #: bool: Whether the image will be saved.
        self.is_save = False

        #: bool: Whether the microscope is acquiring.
        self.is_acquiring = False

        #: dict: Dictionary of different operating modes.
        self.mode_dict = {
            "Continuous Scan": "live",
            "Z-Stack": "z-stack",
            "Single Acquisition": "single",
            "Customized": "customized",
        }

        self.view.pull_down["values"] = list(self.mode_dict.keys())
        self.view.pull_down.current(0)

        # gui event bind
        self.view.acquire_btn.config(command=self.launch_popup_window)
        self.view.pull_down.bind("<<ComboboxSelected>>", self.update_microscope_mode)
        self.view.exit_btn.config(command=self.exit_program)

        # framerate information.
        self.framerate = 0

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
        """

        if images_received == 0:
            if mode == "live" or mode == "customized":
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
        number_of_channels = 0
        for channel in microscope_state["channels"].keys():
            if microscope_state["channels"][channel]["is_selected"] is True:
                number_of_channels += 1

        # Time-lapse acquisition
        number_of_timepoints = int(microscope_state["timepoints"])

        # Multi-Position Acquisition
        if microscope_state["is_multiposition"] is False:
            number_of_positions = 1
        else:
            number_of_positions = len(
                self.parent_controller.configuration["experiment"]["MultiPositions"]
            )

        if mode == "single":
            number_of_slices = 1
        elif mode == "live" or mode == "customized":
            number_of_slices = 1
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
                if mode == "live" or mode == "customized":
                    self.view.CurAcq.start()
                    self.view.OvrAcq.start()
                    self.view.total_acquisition_label.config(text="--:--:--")

                else:
                    # Calculate the number of images remaining.
                    # Time is estimated from the framerate, which includes stage
                    # movement time inherently.
                    try:
                        images_remaining = bottom_anticipated_images - images_received
                        seconds_left = images_remaining / self.framerate
                        self.update_progress_label(seconds_left)
                    except ZeroDivisionError:
                        pass

                if mode == "z-stack":
                    top_percent_complete = 100 * (
                        images_received / top_anticipated_images
                    )

                    self.view.CurAcq["value"] = (
                        top_percent_complete % 100
                        if (top_percent_complete > 100.0)
                        else top_percent_complete
                    )

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

                else:
                    self.view.CurAcq.start()
                    self.view.OvrAcq.start()

            elif stop is True:
                self.update_progress_label(seconds_left=0)
                self.stop_progress_bar()

    def stop_progress_bar(self):
        """Stop moving the continuous progress bar."""
        self.view.CurAcq.stop()
        self.view.OvrAcq.stop()

    def update_progress_label(self, seconds_left):
        """Update the progress label in the Acquire Bar.

        Formatted time is in HH:MM:SS.

        Parameters
        ----------
        seconds_left : int
            Seconds left in the acquisition.
        """
        hours, remainder = divmod(seconds_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.view.total_acquisition_label.config(
            text=f"{int(hours):02}" f":{int(minutes):02}" f":{int(seconds):02}"
        )

    def set_mode(self, mode):
        """Set imaging mode.

        Parameters
        ----------
        mode: str
            Mode could be: 'live', 'z-stack', 'single', 'projection',
        """
        # update pull down combobox
        reverse_dict = dict(map(lambda v: (v[1], v[0]), self.mode_dict.items()))
        if mode not in reverse_dict:
            mode = list(reverse_dict.keys())[0]
        self.mode = mode
        self.view.pull_down.set(reverse_dict[mode])
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "image_mode"
        ] = mode
        self.show_verbose_info("Image mode is set to", mode)

    def get_mode(self):
        """Get the current imaging mode.

        Returns
        -------
        mode : str
            Current imaging mode.
        """
        return self.mode

    def add_mode(self, mode):
        if mode not in self.mode_dict:
            self.mode_dict[mode] = mode
            self.view.pull_down["values"] = list(self.mode_dict.keys())

    def stop_acquire(self):
        """Stop the acquisition."""
        self.stop_progress_bar()
        self.view.acquire_btn.configure(text="Acquire")
        self.view.acquire_btn.configure(state="normal")
        self.view.pull_down.configure(state="normal")
        self.is_acquiring = False

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
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "is_save"
        ] = is_save
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
        if self.is_acquiring and self.view.acquire_btn["text"] == "Acquire":
            return
        if not self.is_acquiring and self.view.acquire_btn["text"] == "Stop":
            return
        if self.view.acquire_btn["text"] == "Stop":
            # tell the controller to stop acquire (continuous mode)
            self.view.acquire_btn.configure(state="disabled")
            self.parent_controller.execute("stop_acquire")

        elif self.is_save and self.mode != "live":
            #: object: Instance of the popup save dialog.
            self.acquire_pop = AcquirePopUp(self.view)
            buttons = (
                self.acquire_pop.get_buttons()
            )  # This holds all the buttons in the popup
            widgets = self.acquire_pop.get_widgets()

            # Configure the button callbacks on the popup window
            buttons["Cancel"].config(command=lambda: self.acquire_pop.popup.dismiss())
            buttons["Done"].config(
                command=lambda: self.launch_acquisition(self.acquire_pop)
            )

            # Configure drop down callbacks, will update save settings when file type is
            # changed
            file_type = widgets["file_type"].get_variable()
            file_type.trace_add("write", lambda *args: self.update_file_type(file_type))

            for k, v in self.saving_settings.items():
                if widgets.get(k, None):
                    widgets[k].set(v)

        else:
            self.is_acquiring = True
            self.view.acquire_btn.configure(state="disabled")
            self.view.pull_down.configure(state="disabled")
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
        # acquire_bar_controller - update image mode
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "image_mode"
        ] = self.mode
        # Update state status of other widgets in the GUI based on what mode is set
        self.parent_controller.channels_tab_controller.set_mode("stop")

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
            self.is_acquiring = True
            self.view.acquire_btn.configure(state="disabled")
            # Close the window
            popup_window.popup.dismiss()
            # tell central controller, save the image/data
            self.parent_controller.execute("acquire_and_save")

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

    def populate_experiment_values(self):
        """Populate the experiment values from the config file.

        Examples
        --------
        >>> populate_experiment_values()
        """
        #: dict: Saving settings.
        self.saving_settings = self.parent_controller.configuration["experiment"][
            "Saving"
        ]
        self.saving_settings["date"] = str(self.saving_settings["date"])
        mode = self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "image_mode"
        ]
        self.set_mode(mode)
        is_save = self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "is_save"
        ]
        self.set_save_option(is_save)

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
