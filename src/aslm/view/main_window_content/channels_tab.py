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
from aslm.view.custom_widgets.hovermixin import HoverButton
from aslm.view.custom_widgets.validation import ValidatedSpinbox, ValidatedCombobox
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ChannelsTab(tk.Frame):
    """Channels Tab for the Main Window

    This tab is used to set the channels for the stack acquisition.

    Parameters
    ----------
    setntbk : tk.Notebook
        The notebook that this tab is added to
    *args : tuple
        Positional arguments for tk.Frame
    **kwargs : dict
        Keyword arguments for tk.Frame

    Attributes
    ----------
    index : int
        The index of the tab in the notebook
    channel_widgets_frame : ChannelCreator
        The frame that contains the channel settings
    stack_acq_frame : StackAcquisitionFrame
        The frame that contains the stack acquisition settings
    stack_timepoint_frame : StackTimePointFrame
        The frame that contains the time settings
    multipoint_frame : MultiPointFrame
        The frame that contains the multipoint settings
    quick_launch : QuickLaunchFrame
        The frame that contains the quick launch buttons
    conpro_acq_frame : ConfocalProjectionFrame
        The frame that contains the confocal projection settings

    Methods
    -------
    None
    """

    def __init__(self, setntbk, *args, **kwargs):
        # Init Frame
        tk.Frame.__init__(self, setntbk, *args, **kwargs)

        self.index = 0

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Channel Settings
        self.channel_widgets_frame = ChannelCreator(self)
        self.channel_widgets_frame.grid(
            row=0, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )

        # Stack Acquisition Settings
        self.stack_acq_frame = StackAcquisitionFrame(self)
        self.stack_acq_frame.grid(
            row=1, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )

        # Time Settings
        self.stack_timepoint_frame = StackTimePointFrame(self)
        self.stack_timepoint_frame.grid(
            row=3, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )

        # Multipoint Enable
        self.multipoint_frame = MultiPointFrame(self)
        self.multipoint_frame.grid(
            row=4, column=0, columnspan=1, sticky=tk.NSEW, padx=10, pady=10
        )

        # Quick Launch Buttons
        self.quick_launch = QuickLaunchFrame(self)
        self.quick_launch.grid(
            row=4, column=1, columnspan=2, sticky=tk.NSEW, padx=10, pady=10
        )

        # Confocal Projection Settings
        self.conpro_acq_frame = ConfocalProjectionFrame(self)
        self.conpro_acq_frame.grid(
            row=5, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )


class ChannelCreator(ttk.Labelframe):
    """Channel Creator

    This frame is used to create the channels for the stack acquisition.

    Parameters
    ----------
    channels_tab : tk.Frame
        The frame that this frame is added to
    *args : tuple
        Positional arguments for ttk.Labelframe
    **kwargs : dict
        Keyword arguments for ttk.Labelframe

    Attributes
    ----------
    title : str
        The title of the frame
    channel_variables : list
        The list of tk.BooleanVar for the channel checkbuttons
    channel_checks : list
        The list of tk.Checkbutton for the channel checkbuttons
    laser_variables : list
        The list of tk.StringVar for the laser pulldowns
    laser_pulldowns : list
        The list of tk.OptionMenu for the laser pulldowns
    add_channel_button : tk.Button
        The button to add a channel
    remove_channel_button : tk.Button
        The button to remove a channel

    Methods
    -------
    None
    """

    def __init__(self, channels_tab, *args, **kwargs):
        #  Init Frame
        self.title = "Channel Settings"
        ttk.Labelframe.__init__(self, channels_tab, text=self.title, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #  Arrays with Widget Variables and widgets themselves
        #  TODO refactor using dicts for variables and one for widgets,
        #   allow access to arrays via a key. might be overly complicated.
        #   Below way is clear just a bit repetitive
        #  Channel Checkbuttons
        self.channel_variables = []
        self.channel_checks = []

        #  Laser Dropdowns
        self.laser_variables = []
        self.laser_pulldowns = []

        #  LaserPower Dropdowns
        self.laserpower_variables = []
        self.laserpower_pulldowns = []

        #  FilterWheel Dropdowns
        self.filterwheel_variables = []
        self.filterwheel_pulldowns = []

        #  Exposure Time Dropdowns
        self.exptime_variables = []
        self.exptime_pulldowns = []

        #  Time Interval Spinboxes
        self.interval_variables = []
        self.interval_spins = []

        # Defocus Spinboxes
        self.defocus_variables = []
        self.defocus_spins = []

        #  Channel Creation

        #  Grids labels them across the top row of each column
        self.label_text = [
            "Channel",
            "Laser",
            "Power",
            "Filter",
            "Exp. Time (ms)",
            "Interval",
            "Defocus",
        ]
        self.labels = []
        self.frame_columns = []

        #  Creates a column frame for each widget,
        # this is to help with the lables lining up
        for idx in range(len(self.label_text)):
            self.frame_columns.append(ttk.Frame(self))
            self.frame_columns[idx].columnconfigure(0, weight=1, uniform=1)
            self.frame_columns[idx].rowconfigure("all", weight=1, uniform=1)
            self.frame_columns[idx].grid(
                row=0, column=idx, sticky=tk.NSEW, padx=1, pady=(4, 6)
            )
            self.labels.append(
                ttk.Label(self.frame_columns[idx], text=self.label_text[idx])
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
                    width=3,
                    font=tk.font.Font(size=11),
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
                    font=tk.font.Font(size=11),
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
                    font=tk.font.Font(size=11),
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
                    width=4,
                    font=tk.font.Font(size=11),
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
    """This class is the frame that holds the stack acquisition settings.

    Parameters
    ----------
    settings_tab : tkinter.Frame
        The frame that holds the settings tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    inputs : dict
        Dictionary of inputs.
    buttons : dict
        Dictionary of buttons.
    pos_slice : tkinter.Frame
        Frame that holds the position slice inputs.
    cycling : tkinter.Frame
        Frame that holds the cycling inputs.
    start_label : tkinter.Label
        Label for the start position slice inputs.
    end_label : tkinter.Label
        Label for the end position slice inputs.

    Methods
    -------
    get_buttons()
        Returns the buttons dictionary.
    get_variables()
        Returns the variables dictionary.
    get_widgets()
        Returns the widgets dictionary.
    """

    def __init__(self, settings_tab, *args, **kwargs):
        # Init Frame
        text_label = "Stack Acquisition Settings (" + "\N{GREEK SMALL LETTER MU}" + "m)"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets and buttons
        self.inputs = {}
        self.buttons = {}

        # Frames for widgets
        self.pos_slice = ttk.Frame(self)
        self.cycling = ttk.Frame(self)

        # Gridding Each Holder Frame
        self.pos_slice.grid(row=0, column=0, sticky=tk.NSEW)
        self.cycling.grid(row=1, column=0, sticky=tk.NSEW)

        # Start Pos Frame (Vertically oriented)
        start_names = ["start_position", "start_focus"]
        start_labels = ["Pos", "Foc"]
        self.start_label = ttk.Label(self.pos_slice, text="Start")
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
        self.end_label = ttk.Label(self.pos_slice, text="End")
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

        Parameters
        ----------
        None

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
        """Returns a dictionary of the widgets

        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of the widgets in the widget
        """
        return self.inputs

    def get_buttons(self):
        """Returns a dictionary of the buttons

        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of the buttons in the widget
        """
        return self.buttons


class StackTimePointFrame(ttk.Labelframe):
    """Frame for the stack timepoint settings

    This class is a frame that holds the widgets for the stack timepoint settings.
    It is a subclass of ttk.Labelframe.

    Parameters
    ----------
    settings_tab : tk.Frame
        The frame that the stack timepoint frame will be placed in
    *args : tuple
        Variable length argument list
    **kwargs : dict
        Arbitrary keyword arguments

    Attributes
    ----------
    inputs : dict
        Dictionary of the widgets in the frame
    buttons : dict
        Dictionary of the buttons in the frame

    Methods
    -------
    get_variables()
        Returns a dictionary of the variables in the widget
    get_widgets()
        Returns a dictionary of the widgets in the widget
    """

    def __init__(self, settings_tab, *args, **kwargs):
        text_label = "Timepoint Settings"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Widget dictionary
        self.inputs = {}

        # Save Data Label
        self.laser_label = ttk.Label(self, text="Save Data")
        self.laser_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(4, 5), pady=(4, 0))

        # Save Data Checkbox
        self.save_data = tk.BooleanVar()
        self.save_data.set(False)
        self.save_check = ttk.Checkbutton(self, text="", variable=self.save_data)
        self.save_check.grid(row=0, column=1, sticky=tk.NSEW, pady=(4, 0))
        self.inputs["save_check"] = self.save_check

        # Timepoints Label, spinbox defaults to 1.
        self.filterwheel_label = ttk.Label(self, text="Timepoints")
        self.filterwheel_label.grid(
            row=1, column=0, sticky=tk.NSEW, padx=(4, 5), pady=2
        )
        self.exp_time_spinval = tk.StringVar()
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
        self.exp_time_label = ttk.Label(self, text="Stack Acq. Time")
        self.exp_time_label.grid(row=2, column=0, sticky=tk.NSEW, padx=(4, 5), pady=2)

        # Stack Acq. Time Spinbox
        self.stack_acq_spinval = tk.StringVar()
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
        self.exp_time_label = ttk.Label(self, text="Stack Pause (s)")
        self.exp_time_label.grid(row=0, column=2, sticky=tk.NSEW, padx=(4, 5), pady=2)

        # Stack Pause Spinbox
        self.stack_pause_spinval = tk.StringVar()
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
        self.exp_time_label = ttk.Label(self, text="Timepoint Interval (hh:mm:ss)")
        self.exp_time_label.grid(row=1, column=2, sticky=tk.NSEW, padx=(4, 5), pady=2)

        # Timepoint Interval Spinbox
        self.timepoint_interval_spinval = tk.StringVar()
        if self.timepoint_interval_spinval.get() == "":
            self.timepoint_interval_spinval.set("0")
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
        self.exp_time_label = ttk.Label(self, text="Experiment Duration (hh:mm:ss)")
        self.exp_time_label.grid(
            row=2, column=2, sticky=tk.NSEW, padx=(4, 5), pady=(2, 6)
        )

        # Total Time Spinbox
        self.total_time_spinval = tk.StringVar()
        if self.total_time_spinval.get() == "":
            self.total_time_spinval.set("0")
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

        Parameters
        ----------
        None

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

        Parameters
        ----------
        None

        Returns
        -------
        widgets : dict
            A dictionary of all the widgets that are tied to each widget name.
        """
        return self.inputs


class MultiPointFrame(ttk.Labelframe):
    def __init__(self, settings_tab, *args, **kwargs):
        text_label = "Multi-Position Acquisition"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Save Data Label
        self.laser_label = ttk.Label(self, text="Enable")
        self.laser_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(4, 4), pady=(4, 4))

        # Save Data Checkbox
        self.on_off = tk.BooleanVar()
        self.save_check = ttk.Checkbutton(self, text="", variable=self.on_off)
        self.save_check.grid(row=0, column=1, sticky=tk.NSEW, pady=(4, 4))

        # Tiling Wizard Button
        self.buttons = {}
        self.buttons["tiling"] = ttk.Button(self, text="Launch Tiling Wizard")
        self.buttons["tiling"].grid(
            row=0, column=2, sticky=tk.NSEW, padx=(10, 0), pady=(4, 4)
        )

    def get_variables(self):
        """Returns a dictionary of all the variables that are tied to each widget name.

        The key is the widget name, value is the variable associated.

        Parameters
        ----------
        None

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

        Parameters
        ----------
        None

        Returns
        -------
        widgets : dict
            A dictionary of all the widgets that are tied to each widget name.
        """
        return self.inputs


class QuickLaunchFrame(ttk.Labelframe):
    """Quick Launch Buttons Frame

    This frame contains buttons that launch the Tiling Wizard.

    Parameters
    ----------
    settings_tab : object
        The settings tab object that this frame is being added to.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    buttons : dict
        A dictionary of all the buttons that are tied to each button name.

    Methods
    -------
    None
    """

    def __init__(self, settings_tab, *args, **kwargs):
        text_label = "Quick Launch Buttons"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Tiling Wizard Button
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

    Parameters
    ----------
    settings_tab : tkinter.ttk.Frame
        The frame that this frame will be placed in.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Attributes
    ----------
    inputs : dict
        Dictionary of widgets and buttons.
    pos_slice : tkinter.ttk.Frame
        Frame for widgets related to position and slice settings.
    cycling : tkinter.ttk.Frame
        Frame for widgets related to cycling settings.
    scanrange_label : tkinter.ttk.Label
        Label for the scan range spinbox.

    Methods
    -------
    get_variables()
        Returns a dictionary of the variables for the widgets in this frame.
    get_widgets()
        Returns a dictionary of the widgets in this frame.
    """

    def __init__(self, settings_tab, *args, **kwargs):
        # Init Frame
        text_label = (
            "Confocal Projection Settings (" + "\N{GREEK SMALL LETTER MU}" + "m)"
        )
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets and buttons
        self.inputs = {}

        # Frames for widgets
        self.pos_slice = ttk.Frame(self)
        self.cycling = ttk.Frame(self)

        # Gridding Each Holder Frame
        self.pos_slice.grid(row=0, column=0, sticky=tk.NSEW)
        self.cycling.grid(row=1, column=0, sticky=tk.NSEW)

        # ScanRange Label, Spinbox
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

        Parameters
        ----------
        None

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

        Parameters
        ----------
        None

        Returns
        -------
        self.inputs : dict
            Dictionary of the widgets in this frame.
        """
        return self.inputs
