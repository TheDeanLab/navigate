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
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.validation import ValidatedSpinbox
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class WaveformParameterPopupWindow:
    """Popup window with waveform parameters for galvos, remote focusing, etc."""

    def __init__(self, root, configuration_controller, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        #: PopUp: The popup window
        self.popup = PopUp(
            root, "Waveform Parameter Settings", "+320+180", top=False, transient=False
        )

        #: configuration_controller: The configuration controller
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

        #: dict: Dictionary for all the variables
        self.inputs = {}
        #: dict: Dictionary for all the buttons
        self.buttons = {}

        # Frames for widgets
        #: ttk.Frame: Frame for mode and magnification
        self.mode_mag_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        #: ttk.Frame: Frame for saving waveform parameters
        self.save_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        #: ttk.LabelFrame: Frame for remote focus parameters
        self.remote_focus_frame = ttk.LabelFrame(
            content_frame, text="Remote Focus", padding=(0, 0, 0, 0)
        )
        #: ttk.LabelFrame: Frame for galvo parameters
        self.galvo_frame = ttk.LabelFrame(
            content_frame, text="Galvo", padding=(0, 0, 0, 0)
        )
        #: ttk.LabelFrame: Frame for waveform
        self.waveform_frame = ttk.LabelFrame(
            content_frame, text="Waveform Setting", padding=(0, 0, 0, 0)
        )

        # Griding Frames
        self.mode_mag_frame.grid(row=0, column=0, sticky=tk.NSEW, pady=(10, 0))
        self.save_frame.grid(row=0, column=3, sticky=tk.NE, padx=10, pady=(10, 0))
        self.remote_focus_frame.grid(
            row=2, column=0, columnspan=4, sticky=tk.NSEW, padx=10, pady=(10, 0)
        )
        self.galvo_frame.grid(
            row=3, column=0, columnspan=4, sticky=tk.NSEW, padx=10, pady=(10, 0)
        )
        self.waveform_frame.grid(
            row=4, column=0, columnspan=4, sticky=tk.NSEW, padx=10, pady=10
        )

        # Filling Frames with widgets
        # Mode/Mag Frame
        self.inputs["Mode"] = LabelInput(
            parent=self.mode_mag_frame,
            label="Mode",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            label_args={"padding": (2, 5, 48, 0)},
        )
        self.inputs["Mode"].grid(row=0, column=0, padx=10)
        self.inputs["Mode"].pad_input(50, 5, 0, 0)
        self.inputs["Mode"].state(["readonly"])

        self.inputs["Mag"] = LabelInput(
            parent=self.mode_mag_frame,
            label="Magnification",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            label_args={"padding": (2, 5, 5, 0)},
        )
        self.inputs["Mag"].grid(row=1, column=0, padx=10)
        self.inputs["Mag"].pad_input(50, 5, 0, 0)
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
        title_labels = ["Laser", "Amplitude", "Offset", "Frequency"]
        # Loop for widgets
        for i in range(len(title_labels)):
            # Title labels
            title = ttk.Label(
                self.remote_focus_frame, text=title_labels[i], padding=(2, 5, 60, 0)
            )
            title.grid(row=0, column=i, sticky=tk.NSEW, padx=(0, 5))
        for i, label in enumerate(laser_labels):
            # Laser labels
            laser = ttk.Label(
                self.remote_focus_frame, text=laser_labels[i], padding=(2, 5, 0, 0)
            )
            laser.grid(row=i + 1, column=0, sticky=tk.NSEW)

            # Entry Widgets
            self.inputs[laser_labels[i] + " Amp"] = LabelInput(
                parent=self.remote_focus_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[laser_labels[i] + " Amp"].grid(
                row=i + 1, column=1, sticky=tk.NSEW, pady=(20, 0), padx=(0, 5)
            )

            self.inputs[laser_labels[i] + " Off"] = LabelInput(
                parent=self.remote_focus_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[laser_labels[i] + " Off"].grid(
                row=i + 1, column=2, sticky=tk.NSEW, pady=(20, 0)
            )

        galvo_labels = list(
            map(lambda i: f"Galvo {i}", range(self.configuration_controller.galvo_num))
        )

        for i, label in enumerate(galvo_labels):
            galvo = ttk.Label(
                self.galvo_frame, text=galvo_labels[i], padding=(2, 5, 53, 0)
            )

            galvo.grid(row=i, column=0, sticky=tk.NSEW)

            self.inputs[galvo_labels[i] + " Amp"] = LabelInput(
                parent=self.galvo_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[galvo_labels[i] + " Amp"].grid(
                row=i, column=1, sticky=tk.NSEW, pady=(10, 0), padx=(0, 5)
            )

            self.inputs[galvo_labels[i] + " Off"] = LabelInput(
                parent=self.galvo_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
            )

            self.inputs[galvo_labels[i] + " Off"].grid(
                row=i, column=2, sticky=tk.NSEW, pady=(10, 0), padx=(0, 5)
            )

            self.inputs[galvo_labels[i] + " Freq"] = LabelInput(
                parent=self.galvo_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"from_": 0, "to": 1000, "increment": 0.1},
            )

            self.inputs[galvo_labels[i] + " Freq"].grid(
                row=i, column=3, sticky=tk.NSEW, pady=(10, 0), padx=(0, 5)
            )

            # Button for automatic estimate of galvo frequency
            self.buttons[galvo_labels[i] + " Freq"] = ttk.Button(
                self.galvo_frame, text="Estimate Frequency", padding=(2, 0, 2, 0)
            )

            self.buttons[galvo_labels[i] + " Freq"].grid(
                row=i, column=4, sticky=tk.NE, pady=(10, 0)
            )

        self.inputs["galvo_info"] = LabelInput(
            parent=self.galvo_frame,
            input_class=ttk.Label,
            input_var=None,
            input_args={"text": "", "state": "disabled"},
        )
        self.inputs["galvo_info"].grid(
            row=len(galvo_labels), column=1, sticky=tk.NW, pady=(10, 0)
        )

        self.inputs["all_channels"] = LabelInput(
            parent=self.galvo_frame,
            input_class=ttk.Checkbutton,
            input_var=tk.BooleanVar(),
            label="Apply To All Channels",
        )
        self.inputs["all_channels"].grid(
            row=len(galvo_labels),
            column=2,
            columnspan=2,
            sticky=tk.NE,
            pady=(10, 0),
            padx=(0, 20),
        )
        self.inputs["all_channels"].widget.config(state="disabled")

        self.buttons["advanced_galvo_setting"] = ttk.Button(
            self.galvo_frame, text="Advanced Setting", padding=(5, 0, 5, 0)
        )
        self.buttons["advanced_galvo_setting"].grid(
            row=len(galvo_labels),
            column=4,
            sticky=tk.NSEW,
            pady=(10, 0),
        )

        # other remote focus waveform setting
        label = ttk.Label(self.waveform_frame, text="Remote Focus")
        label.grid(row=0, columnspan=4, padx=5, sticky=tk.NW, pady=(10, 0))
        separator = ttk.Separator(self.waveform_frame)
        separator.grid(row=1, columnspan=4, sticky=tk.NSEW)
        rf_waveform_labels = [
            "Delay (ms)",
            "Fly Back Time (ms)",
            "Settle Duration (ms)",
            "Percent Smoothing",
        ]
        dict_labels = ["Delay", "Ramp_falling", "Duty", "Smoothing"]
        for i in range(len(dict_labels)):
            label = ttk.Label(
                self.waveform_frame, text=rf_waveform_labels[i], padding=(2, 5, 5, 0)
            )
            label.grid(
                row=i // 2 + 2,
                column=(i % 2) * 2,
                padx=(2 + (i % 2) * 40, 20),
                sticky=tk.NSEW,
            )
            self.inputs[dict_labels[i]] = LabelInput(
                parent=self.waveform_frame,
                input_class=ValidatedSpinbox,
                # label=rf_waveform_labels[i],
                input_var=tk.StringVar(),
                # label_args={"padding": (2, 5, 5, 0)},
                input_args={"from_": 0, "to": 100, "increment": 0.1},
            )
            self.inputs[dict_labels[i]].grid(
                row=i // 2 + 2, column=(i % 2) * 2 + 1, sticky=tk.NSEW
            )
        row_id = 2 + len(rf_waveform_labels) // 2
        label = ttk.Label(self.waveform_frame, text="Camera")
        label.grid(row=row_id, column=0, padx=5, pady=(10, 0), sticky=tk.NW)
        separator = ttk.Separator(self.waveform_frame)
        separator.grid(row=row_id + 1, columnspan=4, sticky=tk.NSEW)
        camera_waveform_labels = ["Delay (ms)", "Settle Duration (ms)"]
        dict_labels = ["camera_delay", "camera_settle_duration"]
        for i in range(len(camera_waveform_labels)):
            label = ttk.Label(
                self.waveform_frame,
                text=camera_waveform_labels[i],
                padding=(2, 5, 5, 0),
            )
            label.grid(
                row=i // 2 + row_id + 2,
                column=(i % 2) * 2,
                padx=(2 + (i % 2) * 40, 20),
                sticky=tk.NSEW,
            )
            self.inputs[dict_labels[i]] = LabelInput(
                parent=self.waveform_frame,
                input_class=ValidatedSpinbox,
                # label=rf_waveform_labels[i],
                input_var=tk.StringVar(),
                # label_args={"padding": (2, 5, 5, 0)},
                input_args={"from_": 0, "to": 100, "increment": 0.1},
            )
            self.inputs[dict_labels[i]].grid(
                row=i // 2 + row_id + 2, column=(i % 2) * 2 + 1, sticky=tk.NSEW
            )

    # Getters
    def get_variables(self):
        """Returns the variables of the inputs

        This function returns a dictionary of all the variables
        that are tied to each widget name.
        The key is the widget name, value is the variable associated.

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

        Returns
        -------
        dict
            Dictionary of all the buttons

        Examples
        --------
        >>> self.get_buttons()
        """
        return self.buttons


class AdvancedWaveformParameterPopupWindow:
    def __init__(self, root, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        #: PopUp: The popup window
        self.popup = PopUp(
            root, "Advanced Galvo Setting", "+320+180", top=False, transient=False
        )

        content_frame = self.popup.get_frame()
        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        self.inputs = {}
        self.buttons = {}
        self.variables = {}

        self.top_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        self.parameter_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))

        self.top_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=(10, 0))
        self.parameter_frame.grid(
            row=1, column=0, sticky=tk.NSEW, padx=10, pady=(10, 0)
        )

        label = ttk.Label(self.top_frame, text="Galvo Parameters Associate with:")
        label.grid(row=0, column=0, columnspan=4, sticky=tk.NW)
        self.variables["galvo_factor"] = tk.StringVar()

        laser = ttk.Radiobutton(
            master=self.top_frame,
            text="Laser Wavelength",
            value="laser",
            variable=self.variables["galvo_factor"],
        )
        channel = ttk.Radiobutton(
            master=self.top_frame,
            text="Channel",
            value="channel",
            variable=self.variables["galvo_factor"],
        )
        none_factor = ttk.Radiobutton(
            master=self.top_frame,
            text="None",
            value="none",
            variable=self.variables["galvo_factor"],
        )
        self.top_frame.grid_columnconfigure(0, minsize=50)
        laser.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=(10, 0))
        channel.grid(row=1, column=2, sticky=tk.NSEW, padx=5, pady=(10, 0))
        none_factor.grid(row=1, column=3, sticky=tk.NSEW, padx=5, pady=(10, 0))

    def generate_paramter_frame(self, factors=["All"], galvos=[]):
        """Generate galvo widgets

        Parameters
        ----------
        factors : list
            A list of galvo factor names
        galvos : list
            A list of galvo amplitude and offset values
        """
        # remove all widgets
        for child in self.parameter_frame.winfo_children():
            child.destroy()

        self.parameters = {}

        if len(galvos) < 3:
            self.parameter_frame.grid_columnconfigure(0, minsize=50)
            for i in range(len(galvos)):
                label = ttk.Label(self.parameter_frame, text=f"Galvo {i}")
                label.grid(row=0, column=i * 2 + 1, columnspan=2, padx=20)

                label = ttk.Label(self.parameter_frame, text="Amplitude")
                label.grid(
                    row=1, column=i * 2 + 1, sticky=tk.NSEW, padx=10, pady=(5, 0)
                )
                label = ttk.Label(self.parameter_frame, text="Offset")
                label.grid(
                    row=1, column=i * 2 + 2, sticky=tk.NSEW, padx=10, pady=(5, 0)
                )

            for i in range(len(factors)):
                label = ttk.Label(self.parameter_frame, text=factors[i])
                label.grid(row=i + 2, column=0, sticky=tk.NSEW, padx=20, pady=5)

                for j in range(len(galvos)):
                    self.parameters[f"galvo_{i}_{j}_amp"] = LabelInput(
                        parent=self.parameter_frame,
                        input_class=ValidatedSpinbox,
                        input_var=tk.StringVar(),
                    )
                    # self.parameters[f"galvo_{i}_{j}_amp"].set(galvos[j][i][0])
                    self.parameters[f"galvo_{i}_{j}_amp"].grid(
                        row=i + 2,
                        column=j * 2 + 1,
                        sticky=tk.NSEW,
                        padx=(0, 5),
                        pady=(0, 5),
                    )

                    self.parameters[f"galvo_{i}_{j}_off"] = LabelInput(
                        parent=self.parameter_frame,
                        input_class=ValidatedSpinbox,
                        input_var=tk.StringVar(),
                    )
                    # self.parameters[f"galvo_{i}_{j}_off"].set(galvos[j][i][1])
                    self.parameters[f"galvo_{i}_{j}_off"].grid(
                        row=i + 2,
                        column=j * 2 + 2,
                        sticky=tk.NSEW,
                        padx=(0, 5),
                        pady=(0, 5),
                    )
        else:
            # using tabs
            notebook = ttk.Notebook(self.parameter_frame)
            notebook.grid(row=0, column=0, padx=10, pady=10)

            for i in range(len(factors)):
                tab = tk.Frame(notebook, width=200)
                notebook.add(tab, text=factors[i])
                tab.grid_columnconfigure(0, minsize=50)
                label = ttk.Label(tab, text="Amplitude")
                label.grid(row=0, column=1, sticky=tk.NSEW, padx=10, pady=5)
                label = ttk.Label(tab, text="Offset")
                label.grid(row=0, column=2, sticky=tk.NSEW, padx=10, pady=5)

                for j in range(len(galvos)):
                    label = ttk.Label(tab, text=f"Galvo {j}")
                    label.grid(
                        row=j + 1, column=0, sticky=tk.NSEW, padx=10, pady=(0, 5)
                    )

                    self.parameters[f"galvo_{i}_{j}_amp"] = LabelInput(
                        parent=tab,
                        input_class=ValidatedSpinbox,
                        input_var=tk.StringVar(),
                    )
                    # self.parameters[f"galvo_{i}_{j}_amp"].set(galvos[j][i][0])
                    self.parameters[f"galvo_{i}_{j}_amp"].grid(
                        row=j + 1, column=1, sticky=tk.NSEW, padx=10, pady=(0, 5)
                    )
                    self.parameters[f"galvo_{i}_{j}_off"] = LabelInput(
                        parent=tab,
                        input_class=ValidatedSpinbox,
                        input_var=tk.StringVar(),
                    )
                    # self.parameters[f"galvo_{i}_{j}_off"].set(galvos[j][i][1])
                    self.parameters[f"galvo_{i}_{j}_off"].grid(
                        row=j + 1, column=2, sticky=tk.NSEW, padx=10, pady=(0, 5)
                    )
