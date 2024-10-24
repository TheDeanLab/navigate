# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, Iterable
import re

# Third Party Imports

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.file_functions import create_save_path
from navigate.view.popups.acquire_popup import AcquirePopUp
from navigate.view.main_window_content.acquire_notebook import AcquireBar


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AcquireBarController(GUIController):
    """Acquire Bar Controller."""

    def __init__(self, view: AcquireBar, parent_controller: Any) -> None:
        """Initialize the Acquire Bar Controller.

        Parameters
        ----------
        view : AcquireBar
            Instance of the View.
        parent_controller : Any
            Instance of the Main Controller.
        """
        super().__init__(view, parent_controller)

        #: AcquirePopUp: Instance of the popup window.
        self.acquire_pop = None

        #: dict: Saving settings.
        self.saving_settings = None

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
        self.view.pull_down.state(["!disabled", "readonly"])

        # gui event bind
        self.view.acquire_btn.config(command=self.launch_popup_window)
        self.view.pull_down.bind("<<ComboboxSelected>>", self.update_microscope_mode)
        self.view.exit_btn.config(command=self.exit_program)

        # framerate information.
        self.framerate = 0

    def progress_bar(
        self,
        images_received: int,
        microscope_state: Dict[str, Any],
        mode: str,
        stop=False,
    ):
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
        elif mode == "z-stack":
            number_of_slices = microscope_state["number_z_steps"]
        else:
            number_of_slices = 1

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
                if mode == "z-stack" or mode == "single":
                    # Calculate the number of images remaining.
                    # Time is estimated from the framerate, which includes stage
                    # movement time inherently.
                    try:
                        images_remaining = bottom_anticipated_images - images_received
                        seconds_left = images_remaining / self.framerate
                        self.update_progress_label(seconds_left)
                    except ZeroDivisionError:
                        pass
                else:
                    self.view.CurAcq.start()
                    self.view.OvrAcq.start()
                    self.view.total_acquisition_label.config(text="--:--:--")

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

    def stop_progress_bar(self) -> None:
        """Stop moving the continuous progress bar."""
        self.view.CurAcq.stop()
        self.view.OvrAcq.stop()

    def update_progress_label(self, seconds_left: int) -> None:
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

    def set_mode(self, mode: str) -> None:
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

    def get_mode(self) -> str:
        """Get the current imaging mode.

        Returns
        -------
        mode : str
            Current imaging mode.
        """
        return self.mode

    def add_mode(self, mode: str) -> None:
        """Add a new mode to the mode dictionary.

        Parameters
        ----------
        mode : str
            Mode to add to the dictionary.
        """
        if mode not in self.mode_dict:
            self.mode_dict[mode] = mode
            self.view.pull_down["values"] = list(self.mode_dict.keys())

    def stop_acquire(self) -> None:
        """Stop the acquisition.

        Stop the progress bar, set the acquire button back to "Acquire", place pull
        down menu in non-disabled format.
        """
        self.stop_progress_bar()
        self.view.acquire_btn.configure(text="Acquire")
        self.view.acquire_btn.configure(state="normal")
        self.view.pull_down.state(["!disabled", "readonly"])
        self.is_acquiring = False

    def set_save_option(self, is_save: bool) -> None:
        """Set whether the image will be saved.

        Parameters
        ----------
        is_save : bool
            True if we will save the data.  False if we will not.
        """
        self.is_save = is_save
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "is_save"
        ] = is_save
        self.show_verbose_info("set save data option:", is_save)

    def launch_popup_window(self) -> None:
        """Launch the Save Dialog Popup Window

        The popup window should only be launched if the microscope is set to save the
        data, except the continuous acquisition mode. The popup window provides the
        user with the opportunity to fill in fields that describe the experiment and
        also dictate the save path of the data in a standardized format.
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
            self.acquire_pop = AcquirePopUp(self.view)

            buttons = self.acquire_pop.get_buttons()
            widgets = self.acquire_pop.get_widgets()

            # Configure the button callbacks on the popup window
            buttons["Cancel"].config(command=lambda: self.acquire_pop.popup.dismiss())
            buttons["Done"].config(
                command=lambda: self.launch_acquisition(self.acquire_pop)
            )
            self.acquire_pop.popup.bind(
                "<Escape>", lambda e: self.acquire_pop.popup.dismiss()
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
            self.view.pull_down.state(["disabled", "readonly"])
            self.parent_controller.execute("acquire")

    def update_microscope_mode(self, *args: Iterable) -> None:
        """Gets the state of the pull-down menu and tells the central controller

        Will additionally call functions to disable and enable widgets based on mode

        Parameters
        ----------
        args : str
            Imaging Mode.
        """
        self.mode = self.mode_dict[self.view.pull_down.get()]
        self.show_verbose_info("The Microscope State is now:", self.get_mode())
        # acquire_bar_controller - update image mode
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "image_mode"
        ] = self.mode
        # Update state status of other widgets in the GUI based on what mode is set
        self.parent_controller.channels_tab_controller.set_mode("stop")

    def update_file_type(self, file_type: tk.StringVar) -> None:
        """Updates the file type when the drop-down in save dialog is changed.

        Parameters
        ----------
        file_type : tk.StringVar
            File type.
        """
        self.saving_settings["file_type"] = file_type.get()

    def launch_acquisition(self, popup_window: AcquirePopUp) -> None:
        """Launch the Acquisition.

        Once the popup window has been filled out, we first create the save path using
        the create_save_path function.
        This automatically removes spaces and replaces them with underscores.
        Then it makes the directory.
        Thereafter, the experiment is ready to go.

        Parameters
        ----------
        popup_window : AcquirePopUp
            Instance of the popup save dialog.
        """
        # update saving settings according to user's input
        self.update_experiment_values(popup_window)

        entry_names = [
            "user",
            "tissue",
            "celltype",
            "label",
            "prefix",
        ]

        for name in entry_names:
            if not self.is_valid_string(self.saving_settings[name]):
                messagebox.showwarning(
                    title="Invalid Entry",
                    message="Only alphanumeric characters, hyphens, "
                            "and underscores are allowed. \n",
                    parent=popup_window.popup,
                )
                return

        # Verify user's input is non-zero.
        is_valid = (
            self.saving_settings["user"]
            and self.saving_settings["tissue"]
            and self.saving_settings["celltype"]
            and self.saving_settings["label"]
        )

        if is_valid:
            # Verify that the path is valid.
            try:
                file_directory = create_save_path(self.saving_settings)
            except Exception:
                messagebox.showwarning(
                    title="Directory Not Found.",
                    message="The directory specified is invalid. \n"
                            "This commonly occurs when the Root Directory is "
                            "incorrect. Please double-check and try again.",
                    parent=popup_window.popup,
                )
                return

            self.is_acquiring = True
            self.view.acquire_btn.configure(state="disabled")
            popup_window.popup.dismiss()
            self.parent_controller.execute("acquire_and_save", file_directory)

    def exit_program(self) -> None:
        """Exit Button to close the program."""
        if messagebox.askyesno("Exit", "Are you sure?"):
            self.show_verbose_info("Exiting Program")
            # call the central controller to stop all the threads
            self.parent_controller.execute("exit")

    def populate_experiment_values(self) -> None:
        """Populate the experiment values from the config file."""
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

    def update_experiment_values(self, popup_window: AcquirePopUp) -> None:
        """Gets the entries from the popup save dialog and overwrites the
        saving_settings dictionary.

        Parameters
        ----------
        popup_window : AcquirePopUp
            Instance of the popup save dialog.
        """
        popup_vals = popup_window.get_variables()
        for name in popup_vals:
            # remove leading and tailing whitespaces
            self.saving_settings[name] = popup_vals[name].strip()

    @staticmethod
    def is_valid_string(string: str) -> bool:
        """Check if the string is valid.

        Parameters
        ----------
        string : str
            String to check.

        Returns
        -------
        bool
            True if the string is valid.
        """
        pattern = r'^[\w\-\ ]+$'
        return bool(re.match(pattern, string))
