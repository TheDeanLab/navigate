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

# Standard Imports
import tkinter as tk
from tkinter import ttk
import logging

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.hovermixin import HoverButton
from navigate.view.custom_widgets.validation import ValidatedSpinbox, ValidatedCombobox
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.style import SpinboxStyle

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ChannelsTab(tk.Frame):
    """Channels Tab for the Main Window

    This tab is used to set the channels for the stack acquisition.
    """

    def __init__(self, setntbk, *args, **kwargs):
        """Initialization of the Channels Tab

        Parameters
        ----------
        setntbk : tk.Notebook
            The notebook that this tab is added to
        *args : tuple
            Positional arguments for tk.Frame
        **kwargs : dict
            Keyword arguments for tk.Frame

        """
        # Init Frame
        tk.Frame.__init__(self, setntbk, *args, **kwargs)

        #: int: The index of the tab
        self.index = 0

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #: ChannelCreator: The frame that holds the channel settings
        self.channel_widgets_frame = ChannelCreator(self)
        self.channel_widgets_frame.grid(
            row=0, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )

        #: StackAcquisitionFrame: The frame that holds the stack acquisition settings
        self.stack_acq_frame = StackAcquisitionFrame(self)
        self.stack_acq_frame.grid(
            row=1, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )

        #: StackTimePointFrame: The frame that holds the time settings
        self.stack_timepoint_frame = StackTimePointFrame(self)
        self.stack_timepoint_frame.grid(
            row=3, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )

        #: MultiPointFrame: The frame that holds the multipoint settings
        self.multipoint_frame = MultiPointFrame(self)
        self.multipoint_frame.grid(
            row=4, column=0, columnspan=1, sticky=tk.NSEW, padx=10, pady=10
        )

        #: QuickLaunchFrame: The frame that holds the quick launch buttons
        self.quick_launch = QuickLaunchFrame(self)
        self.quick_launch.grid(
            row=4, column=1, columnspan=2, sticky=tk.NSEW, padx=10, pady=10
        )

        #: ConfocalProjectionFrame: The frame that holds the confocal projection
        # settings
        self.conpro_acq_frame = ConfocalProjectionFrame(self)
        self.conpro_acq_frame.grid(
            row=5, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )


class ChannelCreator(ttk.Labelframe):
    """Channel Creator

    This frame is used to create the channels for the stack acquisition.
    """

    def __init__(self, channels_tab, *args, **kwargs):
        """ Initialization of the Channel Creator

        Parameters
        ----------
        channels_tab : tk.Frame
            The frame that this frame is added to
        *args : tuple
            Positional arguments for ttk.Labelframe
        **kwargs : dict
            Keyword arguments for ttk.Labelframe
        """
        #: str: The title of the frame
        self.title = "Channel Settings"

        ttk.Labelframe.__init__(self,
                                channels_tab,
                                text=self.title,
                                # style="Custom.TLabelFrame",
                                *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #  Arrays with Widget Variables and widgets themselves
        #  TODO refactor using dicts for variables and one for widgets,
        #   allow access to arrays via a key. might be overly complicated.
        #   Below way is clear just a bit repetitive

        #: list: List of the variables for the channel checkbuttons
        self.channel_variables = []

        #: list: List of the channel checkbuttons
        self.channel_checks = []

        #: list: List of the variables for the laser dropdowns
        self.laser_variables = []

        #: list: List of the laser dropdowns
        self.laser_pulldowns = []

        #: list: List of the variables for the laser power dropdowns
        self.laserpower_variables = []

        #: list: List of the laser power dropdowns
        self.laserpower_pulldowns = []

        #: list: List of the variables for the filterwheel dropdowns
        self.filterwheel_variables = []

        #: list: List of the filterwheel dropdowns
        self.filterwheel_pulldowns = []

        #: list: List of the variables for the exposure time dropdowns
        self.exptime_variables = []

        #: list: List of the exposure time dropdowns
        self.exptime_pulldowns = []

        #: list: List of the variables for the time interval spinboxes
        self.interval_variables = []

        #: list: List of the time interval spinboxes
        self.interval_spins = []

        #: list: List of the variables for the defocus spinboxes
        self.defocus_variables = []

        #: list: List of the defocus spinboxes
        self.defocus_spins = []

        #: list: List of the labels for the columns
        self.label_text = [
            "Channel",
            "Laser",
            "Power",
            "Filter",
            "Exposure",
            "Interval",
            "Defocus",
        ]

        #: list: List of the labels for the columns
        self.labels = []

        #: list: List of the frames for the columns
        self.frame_columns = []

        #  Creates a column frame for each widget,
        # this is to help with the labels lining up
        for idx in range(len(self.label_text)):
            self.frame_columns.append(ttk.Frame(self))
            self.frame_columns[idx].columnconfigure(0, weight=1, uniform=1)
            self.frame_columns[idx].rowconfigure("all", weight=1, uniform=1)
            self.frame_columns[idx].grid(
                row=0, column=idx, sticky=tk.NSEW, padx=1, pady=(4, 6)
            )
            self.labels.append(
                ttk.Label(self.frame_columns[idx],
                          text=self.label_text[idx],
                          )
            )
            self.labels[idx].grid(row=0, column=0, sticky=tk.N, pady=1, padx=1)
        self.frame_columns[5].grid(padx=(1, 4))
        self.frame_columns[0].grid(padx=(4, 1))

        #  Adds and grids widgets to respective column
        #  TODO add connection to config file to specify the range.
        #   This will allow custom selection of amount of channels.
        #   Also may need further refactoring

        for num in range(0, 5):
            #  This will add a widget to each column frame for the respective types
            #  Channel Checkboxes
            self.channel_variables.append(tk.BooleanVar())
            self.channel_checks.append(
                ttk.Checkbutton(
                    self.frame_columns[0],
                    text="CH" + str(num + 1),
                    variable=self.channel_variables[num],
                )
            )
            self.channel_checks[num].grid(
                row=num + 1, column=0, sticky=tk.NSEW, padx=1, pady=1
            )

            #  Laser Dropdowns
            self.laser_variables.append(tk.StringVar())
            self.laser_pulldowns.append(
                ttk.Combobox(
                    self.frame_columns[1],
                    textvariable=self.laser_variables[num],
                    width=6,
                    font=SpinboxStyle().font,
                )
            )
            self.laser_pulldowns[num].state(["readonly"])
            self.laser_pulldowns[num].grid(
                row=num + 1, column=0, sticky=tk.NSEW, padx=1, pady=1
            )

            #  Laser Power Spinbox
            self.laserpower_variables.append(tk.StringVar())
            self.laserpower_pulldowns.append(
                ttk.Spinbox(
                    self.frame_columns[2],
                    from_=0,
                    to=100.0,
                    textvariable=self.laserpower_variables[num],
                    increment=5,
                    width=4,
                    font=SpinboxStyle().font,
                )
            )
            self.laserpower_pulldowns[num].grid(
                row=num + 1, column=0, sticky=tk.NS, padx=1, pady=1
            )

            #  FilterWheel Dropdowns
            self.filterwheel_variables.append(tk.StringVar())
            self.filterwheel_pulldowns.append(
                ttk.Combobox(
                    self.frame_columns[3],
                    textvariable=self.filterwheel_variables[num],
                    width=10,
                    font=SpinboxStyle().font,
                )
            )
            self.filterwheel_pulldowns[num].state(["readonly"])
            self.filterwheel_pulldowns[num].grid(
                row=num + 1, column=0, sticky=tk.NSEW, padx=1, pady=1
            )

            #  Exposure Time Spinboxes
            self.exptime_variables.append(tk.StringVar())
            self.exptime_pulldowns.append(
                ttk.Spinbox(
                    self.frame_columns[4],
                    from_=0,
                    to=5000.0,
                    textvariable=self.exptime_variables[num],
                    increment=25,
                    width=5,
                    font=SpinboxStyle().font,
                )
            )
            self.exptime_pulldowns[num].grid(
                row=num + 1, column=0, sticky=tk.NSEW, padx=1, pady=1
            )

            #  Time Interval Spinboxes
            self.interval_variables.append(tk.StringVar())
            self.interval_spins.append(
                ttk.Spinbox(
                    self.frame_columns[5],
                    from_=0,
                    to=5000.0,
                    textvariable=self.interval_variables[num],
                    increment=1,
                    width=3,
                    font=SpinboxStyle().font,
                )
            )
            self.interval_spins[num].grid(
                row=num + 1, column=0, sticky=tk.NSEW, padx=1, pady=1
            )

            # Defocus Spinbox
            self.defocus_variables.append(tk.DoubleVar())
            self.defocus_spins.append(
                ValidatedSpinbox(
                    self.frame_columns[6],
                    from_=-500.0,
                    to=500.0,
                    textvariable=self.defocus_variables[num],
                    increment=0.1,
                    width=5,
                    font=SpinboxStyle().font,
                )
            )
            self.defocus_spins[num].grid(
                row=num + 1, column=0, sticky=tk.NSEW, padx=1, pady=1
            )

        self.filterwheel_pulldowns[1].grid(pady=2)
        self.filterwheel_pulldowns[2].grid(pady=2)
        self.laser_pulldowns[1].grid(pady=2)
        self.laser_pulldowns[2].grid(pady=2)
        self.channel_checks[1].grid(pady=2)
        self.channel_checks[2].grid(pady=2)


class StackAcquisitionFrame(ttk.Labelframe):
    """This class is the frame that holds the stack acquisition settings."""

    def __init__(self, settings_tab, *args, **kwargs):
        """Initialization of the Stack Acquisition Frame

        Parameters
        ----------
        settings_tab : tkinter.Frame
            The frame that holds the settings tab.
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """
        # Init Frame
        text_label = "Stack Acquisition Settings"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #: dict: Dictionary of the widgets in the frame
        self.inputs = {}

        #: dict: Dictionary of the buttons in the frame
        self.buttons = {}

        #: tkinter.Frame: The frame that holds the position and slice settings
        self.pos_slice = ttk.Frame(self)

        #: tkinter.Frame: The frame that holds the laser cycling settings
        self.cycling = ttk.Frame(self)

        # Griding Each Holder Frame
        self.pos_slice.grid(row=0, column=0, sticky=tk.NSEW)
        self.cycling.grid(row=1, column=0, sticky=tk.NSEW)

        # Start Pos Frame (Vertically oriented)
        start_names = ["start_position", "start_focus"]
        start_labels = ["Pos", "Foc"]

        #: tkinter.Label: The label for the start position frame
        self.start_label = ttk.Label(self.pos_slice, text="Start (" +
                                                          "\N{GREEK SMALL LETTER MU}" +
                                                          "m)")
        # (" + "\N{GREEK SMALL LETTER MU}" + "m)
        self.start_label.grid(row=0, column=0, sticky="S")
        for i in range(len(start_names)):
            self.inputs[start_names[i]] = LabelInput(
                parent=self.pos_slice,
                label=start_labels[i],
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(),
                input_args={"from_": 0.0, "to": 10000, "increment": 0.5, "width": 6},
            )
            self.inputs[start_names[i]].grid(
                row=i + 1, column=0, sticky="N", pady=2, padx=(6, 0)
            )
            self.inputs[start_names[i]].label.grid(sticky="N")

        # Start button
        self.buttons["set_start"] = HoverButton(
            self.pos_slice, text="Set Start Pos/Foc"
        )
        self.buttons["set_start"].grid(row=3, column=0, sticky="N", pady=2, padx=(6, 0))

        # End Pos Frame (Vertically Oriented)
        end_names = ["end_position", "end_focus"]
        end_labels = ["Pos", "Foc"]

        #: tkinter.Label: The label for the end position
        self.end_label = ttk.Label(self.pos_slice, text="End (" +
                                                          "\N{GREEK SMALL LETTER MU}" +
                                                          "m)")

        self.end_label.grid(row=0, column=1, sticky="S")
        for i in range(len(end_names)):
            self.inputs[end_names[i]] = LabelInput(
                parent=self.pos_slice,
                label=end_labels[i],
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(),
                input_args={"from_": 0.0, "to": 10000, "increment": 0.5, "width": 6},
            )
            self.inputs[end_names[i]].grid(
                row=i + 1, column=1, sticky="N", pady=2, padx=(6, 0)
            )
            self.inputs[end_names[i]].label.grid(sticky="N")

        # End Button
        self.buttons["set_end"] = HoverButton(self.pos_slice, text="Set End Pos/Foc")
        self.buttons["set_end"].grid(row=3, column=1, sticky="N", pady=2, padx=(6, 0))

        # Step Size Frame (Vertically oriented)
        #: tkinter.Label: The label for the step size
        self.step_size_label = ttk.Label(self.pos_slice, text="Step Size")
        self.step_size_label.grid(row=0, column=2, sticky="S")
        self.inputs["step_size"] = LabelInput(
            parent=self.pos_slice,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"width": 6},
        )
        self.inputs["step_size"].grid(row=1, column=2, sticky="N", padx=6)

        # Slice Frame (Vertically oriented)
        #: tkinter.Label: The label to add empty space to the slice frame
        self.empty_label = ttk.Label(self.pos_slice, text=" ")
        self.empty_label.grid(row=0, column=3, sticky="N")
        slice_names = ["number_z_steps", "abs_z_start", "abs_z_end"]
        slice_labels = ["# slices      ", "Abs Z Start", "Abs Z Stop"]
        for i in range(len(slice_names)):
            self.inputs[slice_names[i]] = LabelInput(
                parent=self.pos_slice,
                label=slice_labels[i],
                input_class=ttk.Spinbox,
                input_var=tk.DoubleVar(),
                input_args={"increment": 0.5, "width": 6},
            )
            self.inputs[slice_names[i]].widget.configure(state="disabled")
            self.inputs[slice_names[i]].grid(
                row=i + 1, column=3, sticky="NSEW", pady=2, padx=(6, 0)
            )

        # Laser Cycling Settings
        self.inputs["cycling"] = LabelInput(
            parent=self.cycling,
            label="Laser Cycling Settings ",
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            input_args={"width": 8},
        )
        self.inputs["cycling"].state(
            ["readonly"]
        )  # Makes it so the user cannot type a choice into combobox
        self.inputs["cycling"].grid(row=0, column=0, sticky="NSEW", padx=6, pady=5)

        # Initialize DescriptionHovers
        self.inputs["step_size"].widget.hover.setdescription("Step Size")
        self.buttons["set_end"].hover.setdescription("Sets End")

    # Getters
    def get_variables(self):
        """Returns a dictionary of the variables in the widget

        This function returns a dictionary of all the variables
        that are tied to each widget name.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        dict
            Dictionary of the variables in the widget
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Returns a dictionary of the widgets.

        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        dict
            Dictionary of the widgets in the widget
        """
        return self.inputs

    def get_buttons(self):
        """Returns a dictionary of the buttons in the frame.

        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.

        Returns
        -------
        dict
            Dictionary of the buttons in the widget
        """
        return self.buttons


class StackTimePointFrame(ttk.Labelframe):
    """Frame for the stack timepoint settings in the channels tab.

    This class is a frame that holds the widgets for the stack timepoint settings.
    It is a subclass of ttk.Labelframe.
    """

    def __init__(self, settings_tab, *args, **kwargs):
        """Initilization of the Stack Timepoint Frame

        Parameters
        ----------
        settings_tab : tk.Frame
            The frame that the stack timepoint frame will be placed in
        *args : tuple
            Variable length argument list
        **kwargs : dict
            Arbitrary keyword arguments
        """
        text_label = "Timepoint Settings"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Widget dictionary
        #: dict: Dictionary of the widgets in the frame
        self.inputs = {}

        # Save Data Label
        #: tkinter.Label: The label for the save data checkbox
        self.laser_label = ttk.Label(self, text="Save Data")
        self.laser_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(4, 5), pady=(4, 0))

        # Save Data Checkbox
        #: tk.BooleanVar: The variable for the save data checkbox
        self.save_data = tk.BooleanVar()
        self.save_data.set(False)
        #: ttk.Checkbutton: The save data checkbox
        self.save_check = ttk.Checkbutton(self, text="", variable=self.save_data)
        self.save_check.grid(row=0, column=1, sticky=tk.NSEW, pady=(4, 0))
        self.inputs["save_check"] = self.save_check

        # Timepoints Label, spinbox defaults to 1.
        #: tkinter.Label: The label for the timepoints spinbox
        self.filterwheel_label = ttk.Label(self, text="Timepoints")
        self.filterwheel_label.grid(
            row=1, column=0, sticky=tk.NSEW, padx=(4, 5), pady=2
        )
        #: tk.StringVar: The variable for the timepoints spinbox
        self.exp_time_spinval = tk.StringVar()
        #: ttk.Spinbox: The timepoints spinbox
        self.exp_time_spinbox = ttk.Spinbox(
            self,
            from_=0,
            to=5000,
            textvariable=self.exp_time_spinval,
            increment=1,
            width=3,
        )
        self.exp_time_spinbox.grid(row=1, column=1, sticky=tk.NSEW, pady=2)
        self.inputs["time_spin"] = self.exp_time_spinbox

        # Stack Acq. Time Label
        #: tkinter.Label: The label for the stack acquisition time spinbox
        self.exp_time_label = ttk.Label(self, text="Stack Acq. Time")
        self.exp_time_label.grid(row=2, column=0, sticky=tk.NSEW, padx=(4, 5), pady=2)

        # Stack Acq. Time Spinbox
        #: tk.StringVar: The variable for the stack acquisition time spinbox
        self.stack_acq_spinval = tk.StringVar()
        #: ttk.Spinbox: The stack acquisition time spinbox
        self.stack_acq_spinbox = ttk.Spinbox(
            self,
            from_=0,
            to=5000.0,
            textvariable=self.stack_acq_spinval,  # this holds the data in the entry
            increment=25,
            width=6,
        )
        self.stack_acq_spinbox.grid(row=2, column=1, sticky=tk.NSEW, pady=2)
        self.stack_acq_spinbox.state(["disabled"])  # Starts it disabled

        # Stack Pause Label
        #: tkinter.Label: The label for the stack pause spinbox
        self.exp_time_label = ttk.Label(self, text="Stack Pause (s)")
        self.exp_time_label.grid(row=0, column=2, sticky=tk.NSEW, padx=(4, 5), pady=2)

        # Stack Pause Spinbox
        #: tk.StringVar: The variable for the stack pause spinbox
        self.stack_pause_spinval = tk.StringVar()
        #: ttk.Spinbox: The stack pause spinbox
        self.stack_pause_spinbox = ttk.Spinbox(
            self,
            from_=0,
            to=5000.0,
            textvariable=self.stack_pause_spinval,
            increment=25,
            width=6,
        )
        self.stack_pause_spinbox.grid(row=0, column=3, sticky=tk.NSEW, pady=2)
        self.inputs["stack_pause"] = self.stack_pause_spinbox

        # Timepoint Interval Label
        #: tkinter.Label: The label for the timepoint interval spinbox
        self.exp_time_label = ttk.Label(self, text="Time Interval (hh:mm:ss)")
        self.exp_time_label.grid(row=1, column=2, sticky=tk.NSEW, padx=(4, 5), pady=2)

        # Timepoint Interval Spinbox
        #: tk.StringVar: The variable for the timepoint interval spinbox
        self.timepoint_interval_spinval = tk.StringVar()
        if self.timepoint_interval_spinval.get() == "":
            self.timepoint_interval_spinval.set("0")
        #: ttk.Spinbox: The timepoint interval spinbox
        self.timepoint_interval_spinbox = ttk.Spinbox(
            self,
            from_=0,
            to=5000.0,
            textvariable=self.timepoint_interval_spinval,
            increment=25,
            width=6,
        )
        self.timepoint_interval_spinbox.grid(row=1, column=3, sticky=tk.NSEW, pady=2)
        self.timepoint_interval_spinbox.state(["disabled"])  # Starts it disabled

        # Total Time Label
        #: tkinter.Label: The label for the total time spinbox
        self.exp_time_label = ttk.Label(self, text="Experiment Duration (hh:mm:ss)")
        self.exp_time_label.grid(
            row=2, column=2, sticky=tk.NSEW, padx=(4, 5), pady=(2, 6)
        )

        # Total Time Spinbox
        #: tk.StringVar: The variable for the total time spinbox
        self.total_time_spinval = tk.StringVar()
        if self.total_time_spinval.get() == "":
            self.total_time_spinval.set("0")
        #: ttk.Spinbox: The total time spinbox
        self.total_time_spinval = ttk.Spinbox(
            self,
            from_=0,
            to=5000.0,
            textvariable=self.total_time_spinval,
            increment=25,
            width=6,
        )
        self.total_time_spinval.grid(row=2, column=3, sticky=tk.NSEW, pady=(2, 6))
        self.total_time_spinval.state(["disabled"])

    # Getters
    def get_variables(self):
        """Returns a dictionary of all the variables that are tied to each widget name.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        variables : dict
            A dictionary of all the variables that are tied to each widget name.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Returns a dictionary of all the widgets that are tied to each widget name.

        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        widgets : dict
            A dictionary of all the widgets that are tied to each widget name.
        """
        return self.inputs


class MultiPointFrame(ttk.Labelframe):
    """Multi-Position Acquisition Frame"""

    def __init__(self, settings_tab, *args, **kwargs):
        """Initilization of the Multi-Position Acquisition Frame

        Parameters
        ----------
        settings_tab : tk.Frame
            The frame that the multipoint frame will be placed in
        *args : tuple
            Variable length argument list
        **kwargs : dict
            Arbitrary keyword arguments
        """
        text_label = "Multi-Position Acquisition"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Save Data Label
        #: tkinter.Label: The label for the save data checkbox
        self.laser_label = ttk.Label(self, text="Enable")
        self.laser_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(4, 4), pady=(4, 4))

        # Save Data Checkbox
        #: tk.BooleanVar: The variable for the save data checkbox
        self.on_off = tk.BooleanVar()
        #: ttk.Checkbutton: The save data checkbox
        self.save_check = ttk.Checkbutton(self, text="", variable=self.on_off)
        self.save_check.grid(row=0, column=1, sticky=tk.NSEW, pady=(4, 4))

        # Tiling Wizard Button
        #: dict: Dictionary of the buttons in the frame
        self.buttons = {}
        self.buttons["tiling"] = ttk.Button(self, text="Launch Tiling Wizard")
        self.buttons["tiling"].grid(
            row=0, column=2, sticky=tk.NSEW, padx=(10, 0), pady=(4, 4)
        )

    def get_variables(self):
        """Returns a dictionary of all the variables that are tied to each widget name.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        variables : dict
            A dictionary of all the variables that are tied to each widget name.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Returns a dictionary of all the widgets that are tied to each widget name.

        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        widgets : dict
            A dictionary of all the widgets that are tied to each widget name.
        """
        return self.inputs


class QuickLaunchFrame(ttk.Labelframe):
    """Quick Launch Buttons Frame

    This frame contains buttons that launch the Tiling Wizard.
    """

    def __init__(self, settings_tab, *args, **kwargs):
        """Initilization of the Quick Launch Buttons Frame

        Parameters
        ----------
        settings_tab : object
            The settings tab object that this frame is being added to.
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """
        text_label = "Quick Launch Buttons"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Tiling Wizard Button
        #: dict: Dictionary of the buttons in the frame
        self.buttons = {
            "waveform_parameters": ttk.Button(self, text="Waveform Parameters")
        }
        self.buttons["waveform_parameters"].grid(
            row=0, column=2, sticky=tk.NSEW, padx=(4, 4), pady=(4, 4)
        )

        self.buttons["autofocus_button"] = ttk.Button(self, text="Autofocus Settings")
        self.buttons["autofocus_button"].grid(
            row=1, column=2, sticky=tk.NSEW, padx=(4, 4), pady=(4, 4)
        )


class ConfocalProjectionFrame(ttk.Labelframe):
    """Confocal Projection Acquisition Frame

    This frame contains the widgets for the confocal projection acquisition settings.
    """

    def __init__(self, settings_tab, *args, **kwargs):
        """Initilization of the Confocal Projection Frame

        Parameters
        ----------
        settings_tab : tkinter.ttk.Frame
            The frame that this frame will be placed in.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        # Init Frame
        text_label = (
            "Confocal Projection Settings (" + "\N{GREEK SMALL LETTER MU}" + "m)"
        )
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets and buttons
        #: dict: Dictionary of the widgets in the frame
        self.inputs = {}

        # Frames for widgets
        #: tkinter.Frame: The frame that holds the position and slice settings
        self.pos_slice = ttk.Frame(self)
        #: tkinter.Frame: The frame that holds the laser cycling settings
        self.cycling = ttk.Frame(self)

        # Grid Each Holder Frame
        self.pos_slice.grid(row=0, column=0, sticky=tk.NSEW)
        self.cycling.grid(row=1, column=0, sticky=tk.NSEW)

        # ScanRange Label, Spinbox
        #: tkinter.Label: The label for the scan range spinbox
        self.scanrange_label = ttk.Label(self.pos_slice, text="Scan Range")
        self.scanrange_label.grid(row=0, column=0, sticky="S")
        self.inputs["scanrange"] = LabelInput(
            parent=self.pos_slice,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"from_": 0.0, "to": 100000, "increment": 0.5, "width": 6},
        )
        self.inputs["scanrange"].grid(row=0, column=1, sticky="N", padx=6)
        self.inputs["scanrange"].label.grid(sticky="N")

        # Plane Number Label, spinbox defaults to 1.
        #: tkinter.Label: The label for the plane number spinbox
        self.n_plane = ttk.Label(self.pos_slice, text="# planes")
        self.n_plane.grid(row=1, column=0, sticky="S")
        self.inputs["n_plane"] = LabelInput(
            parent=self.pos_slice,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"from_": 1, "to": 100000, "increment": 1, "width": 6},
        )
        self.inputs["n_plane"].grid(row=1, column=1, sticky="N", padx=6)
        self.inputs["n_plane"].label.grid(sticky="N")

        # Offset Start Label, spinbox
        #: tkinter.Label: The label for the offset start spinbox
        self.offset_start = ttk.Label(self.pos_slice, text="Offset Start")
        self.offset_start.grid(row=0, column=2, sticky="S")
        self.inputs["offset_start"] = LabelInput(
            parent=self.pos_slice,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"from_": -300.0, "to": 100000, "increment": 0.1, "width": 6},
        )
        self.inputs["offset_start"].grid(row=0, column=3, sticky="N", padx=6)
        self.inputs["offset_start"].label.grid(sticky="N")

        # Offset End Label, spinbox
        #: tkinter.Label: The label for the offset end spinbox
        self.offset_end = ttk.Label(self.pos_slice, text="Offset End")
        self.offset_end.grid(row=1, column=2, sticky="S")
        self.inputs["offset_end"] = LabelInput(
            parent=self.pos_slice,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"from_": -300.0, "to": 100000, "increment": 0.1, "width": 6},
        )
        self.inputs["offset_end"].grid(row=1, column=3, sticky="N", padx=6)
        self.inputs["offset_end"].label.grid(sticky="N")

        # Laser Cycling Settings
        self.inputs["cycling"] = LabelInput(
            parent=self.cycling,
            label="Laser Cycling Settings ",
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            input_args={"width": 8},
        )
        self.inputs["cycling"].state(
            ["readonly"]
        )  # Makes it so the user cannot type a choice into combobox
        self.inputs["cycling"].grid(row=2, column=2, sticky="NSEW", padx=6, pady=5)

    # Getters
    def get_variables(self):
        """Returns a dictionary of the variables for the widgets in this frame.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        variables : dict
            Dictionary of the variables for the widgets in this frame.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Returns a dictionary of the widgets in this frame.

        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        self.inputs : dict
            Dictionary of the widgets in this frame.
        """
        return self.inputs
