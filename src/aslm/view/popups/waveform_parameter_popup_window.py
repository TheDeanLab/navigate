# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

import tkinter as tk
from tkinter import ttk
from aslm.view.custom_widgets.popup import PopUp
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.validation import ValidatedSpinbox
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class WaveformParameterPopupWindow:
    """Popup window with waveform parameters for galvos, remote focusing, etc.

    Parameters
    ----------
    root : tkinter.Tk
        The root window.
    configuration_controller : ConfigurationController
        The configuration controller.
    *args : tuple
        Positional arguments.
    **kwargs : dict
        Keyword arguments.

    Attributes
    ----------
    inputs : dict
        The input widgets.
    buttons : dict
        The buttons.

    Methods
    -------
    get_variables()
        This function returns a dictionary of all the variables
        that are tied to each widget name.
        The key is the widget name, value is the variable associated.
    get_widgets()
        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
    get_buttons()
        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.
    """

    def __init__(self, root, configuration_controller, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        self.popup = PopUp(
            root, "Waveform Parameter Settings", "+320+180", top=False, transient=False
        )

        self.configuration_controller = configuration_controller

        # Storing the content frame of the popup, this will be the parent of
        # the widgets
        content_frame = self.popup.get_frame()
        content_frame.columnconfigure(0, pad=5)
        content_frame.columnconfigure(1, pad=5)
        content_frame.rowconfigure(0, pad=5)
        content_frame.rowconfigure(1, pad=5)
        content_frame.rowconfigure(2, pad=5)

        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        """Creating the widgets for the popup"""
        # Dictionary for all the variables
        self.inputs = {}
        self.buttons = {}

        # Frames for widgets
        self.mode_mag_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        self.save_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        self.laser_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        self.high_low_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))

        # Griding Frames
        self.mode_mag_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.save_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self.laser_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)
        self.high_low_frame.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW)

        # Filling Frames with widgets
        # Mode/Mag Frame
        self.inputs["Mode"] = LabelInput(
            parent=self.mode_mag_frame,
            label="Mode",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            label_args={"padding": (2, 5, 48, 0)},
        )
        self.inputs["Mode"].grid(row=0, column=0)
        self.inputs["Mode"].state(["readonly"])

        self.inputs["Mag"] = LabelInput(
            parent=self.mode_mag_frame,
            label="Magnification",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            label_args={"padding": (2, 5, 5, 0)},
        )
        self.inputs["Mag"].grid(row=1, column=0)
        self.inputs["Mag"].state(["readonly"])

        # Save Waveform Parameters Frame
        self.buttons["Save"] = ttk.Button(self.save_frame, text="Save Configuration")
        self.buttons["Save"].grid(
            row=0, column=0, sticky=tk.NSEW, padx=(5, 0), pady=(0, 0)
        )

        # Toggle Waveform Button
        self.buttons["toggle_waveform_button"] = ttk.Button(
            self.save_frame,
            text="Disable Waveforms",
        )
        self.buttons["toggle_waveform_button"].grid(
            row=1, column=0, sticky=tk.NSEW, padx=(5, 0), pady=(0, 0)
        )

        # Laser Frame
        laser_labels = self.configuration_controller.lasers_info
        title_labels = ["Laser", "Amplitude", "Offset"]
        # Loop for widgets
        for i in range(3):
            # Title labels
            title = ttk.Label(
                self.laser_frame, text=title_labels[i], padding=(2, 5, 0, 0)
            )
            title.grid(row=0, column=i, sticky=tk.NSEW, padx=(0, 5))
        for i, label in enumerate(laser_labels):
            # Laser labels
            laser = ttk.Label(
                self.laser_frame, text=laser_labels[i], padding=(2, 5, 0, 0)
            )
            laser.grid(row=i + 1, column=0, sticky=tk.NSEW)

            # Entry Widgets
            self.inputs[laser_labels[i] + " Amp"] = LabelInput(
                parent=self.laser_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[laser_labels[i] + " Amp"].grid(
                row=i + 1, column=1, sticky=tk.NSEW, pady=(20, 0), padx=(0, 5)
            )

            self.inputs[laser_labels[i] + " Off"] = LabelInput(
                parent=self.laser_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[laser_labels[i] + " Off"].grid(
                row=i + 1, column=2, sticky=tk.NSEW, pady=(20, 0)
            )

        galvo_labels = list(
            map(lambda i: f"Galvo {i}", range(self.configuration_controller.galvo_num))
        )

        prev = len(laser_labels)

        for i, label in enumerate(galvo_labels):
            galvo = ttk.Label(
                self.laser_frame, text=galvo_labels[i], padding=(2, 5, 0, 0)
            )

            galvo.grid(row=prev + 1, column=0, sticky=tk.NSEW)

            self.inputs[galvo_labels[i] + " Amp"] = LabelInput(
                parent=self.laser_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[galvo_labels[i] + " Amp"].grid(
                row=prev + 1, column=1, sticky=tk.NSEW, pady=(20, 0), padx=(0, 5)
            )

            self.inputs[galvo_labels[i] + " Off"] = LabelInput(
                parent=self.laser_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[galvo_labels[i] + " Off"].grid(
                row=prev + 1, column=2, sticky=tk.NSEW, pady=(20, 0)
            )

            galvo_freq = ttk.Label(
                self.laser_frame, text=galvo_labels[i] + " Freq", padding=(2, 5, 0, 0)
            )

            galvo_freq.grid(row=prev + 2, column=0, sticky=tk.NSEW)

            self.inputs[galvo_labels[i] + " Freq"] = LabelInput(
                parent=self.laser_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"from_": 0, "to": 1000, "increment": 0.1},
            )

            self.inputs[galvo_labels[i] + " Freq"].grid(
                row=prev + 2, column=1, sticky=tk.NSEW, pady=(20, 0)
            )

            prev = prev + 2

        # High/Low Resolution
        hi_lo_labels = ["Percent Delay", "Percent Smoothing", "Duty Wait Duration (ms)"]
        dict_labels = ["Delay", "Smoothing", "Duty"]
        for i in range(3):
            self.inputs[dict_labels[i]] = LabelInput(
                parent=self.high_low_frame,
                input_class=ValidatedSpinbox,
                label=hi_lo_labels[i],
                input_var=tk.StringVar(),
                label_args={"padding": (2, 5, 5, 0)},
                input_args={"from_": 0, "to": 100, "increment": 0.1},
            )
            self.inputs[dict_labels[i]].grid(
                row=i, column=0, sticky=tk.NSEW, padx=(2, 5)
            )

        # Padding Entry Widgets
        self.inputs["Delay"].pad_input(60, 0, 0, 0)
        self.inputs["Smoothing"].pad_input(30, 0, 0, 0)
        self.inputs["Duty"].pad_input(5, 0, 0, 0)

    # Getters
    def get_variables(self):
        """Returns the variables of the inputs

        This function returns a dictionary of all the variables
        that are tied to each widget name.
        The key is the widget name, value is the variable associated.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of all the variables tied to each widget name

        Examples
        --------
        >>> self.get_variables()
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Returns the widgets

        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of all the widgets

        Examples
        --------
        >>> self.get_widgets()
        """
        return self.inputs

    def get_buttons(self):
        """Returns the buttons

        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of all the buttons

        Examples
        --------
        >>> self.get_buttons()
        """
        return self.buttons
