# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
from typing import Dict
from pathlib import Path

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.hover import HoverButton
from navigate.view.custom_widgets.validation import ValidatedSpinbox, ValidatedCombobox
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.common import uniform_grid
import navigate

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ChannelsTab(tk.Frame):
    """Channels Tab for the Main Window

    This tab is used to set the channels for the stack acquisition.
    """

    def __init__(
        self,
        settings_notebook: "navigate.view.main_window_content.settings_notebook.SettingsNotebook",
        *args: list,
        **kwargs: dict,
    ):
        """Initialization of the Channels Tab

        Parameters
        ----------
        settings_notebook : SettingsNotebook
            The notebook that this tab is added to
        *args : list
            Positional arguments for tk.Frame
        **kwargs : dict
            Keyword arguments for tk.Frame

        """
        # Init Frame
        tk.Frame.__init__(self, settings_notebook, *args, **kwargs)

        #: int: The index of the tab
        self.index = 0

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


class ChannelCreator(ttk.Labelframe):
    """Channel Creator

    This frame is used to create the channels for the stack acquisition.
    """

    def __init__(
        self,
        channels_tab: "navigate.view.main_window_content.settings_notebook.SettingsNotebook",
        *args: list,
        **kwargs: dict,
    ) -> None:
        """Initialization of the Channel Creator

        Parameters
        ----------
        channels_tab : tk.Frame
            The frame that this frame is added to
        *args : list
            Positional arguments for ttk.Labelframe
        **kwargs : dict
            Keyword arguments for ttk.Labelframe
        """
        #: str: The title of the frame
        self.title = "Channel Settings"
        ttk.Labelframe.__init__(self, channels_tab, text=self.title, *args, **kwargs)

        #: int: The default padding for widgets in the x direction
        self.pad_x = 1

        #: int: The default padding for widgets in the y direction
        self.pad_y = 1

        #: list: List of the variables for the channel check buttons
        self.channel_variables = []

        #: list: List of the channel check buttons
        self.channel_checks = []

        #: list: List of the variables for the laser dropdowns
        self.laser_variables = []

        #: list: List of the laser dropdowns
        self.laser_pulldowns = []

        #: list: List of the variables for the laser power dropdowns
        self.laserpower_variables = []

        #: list: List of the laser power dropdowns
        self.laserpower_pulldowns = []

        #: list: List of the variables for the filter wheel dropdowns
        self.filterwheel_variables = []

        #: list: List of the filter wheel dropdowns
        self.filterwheel_pulldowns = []

        #: list: List of the variables for the exposure time dropdowns
        self.exptime_variables = []

        #: list: List of the exposure time dropdowns
        self.exptime_pulldowns = []

        #: list: List of the variables for the time interval spin boxes
        self.interval_variables = []

        #: list: List of the time interval spin boxes
        self.interval_spins = []

        #: list: List of the variables for the defocus spin boxes
        self.defocus_variables = []

        #: list: List of the defocus spin boxes
        self.defocus_spins = []

        #: list: List of the labels for the columns
        self.label_text = [
            "Channel",
            "Laser",
            "Power",
            "Filter",
            "Exp. Time (ms)",
            "Interval",
            "Defocus",
        ]

        #: list: List of the labels for the columns
        self.labels = []

        #: list: List of the frames for the columns
        self.frame_columns = []

    def populate_frame(
        self,
        channels: int,
        filter_wheels: int,
        filter_wheel_names: list,
        filter_wheel_types: list = None,
        filter_wheel_visibility: list = None,
    ) -> None:
        """Populates the frame with the widgets.

        This function populates the frame with the widgets for the channels. By updating
        the self.label_text list, the columns can be changed. This function is called
        when the frame is initialized, and when the number of channels is changed in the
        controller.

        Parameters
        ----------
        channels : int
            The number of channels to be added to the frame.
        filter_wheels : int
            The number of filter wheels
        filter_wheel_names : list
            The names of the filter wheels
        filter_wheel_types : list
            The types of filter wheels
        filter_wheel_visibility : list
            Indicates whether each filter wheel belongs to this microscope
        """
        self.reset_frame()

        self.create_labels(
            filter_wheel_names,
            filter_wheels,
            filter_wheel_types,
            filter_wheel_visibility,
        )

        # Configure the columns for consistent spacing
        for i in range(len(self.label_text)):
            self.columnconfigure(i, weight=1)
        for i in range(channels):
            self.rowconfigure(i, weight=1, uniform="1")

        # Creates the widgets for each channel - populates the rows.
        for num in range(0, channels):
            self.channel_variables.append(tk.BooleanVar())
            self.channel_checks.append(
                ttk.Checkbutton(
                    self, text="CH" + str(num + 1), variable=self.channel_variables[num]
                )
            )
            self.channel_checks[num].grid(
                row=num + 1,
                column=(column_id := 0),
                sticky=tk.NSEW,
                padx=self.pad_x,
                pady=self.pad_y,
            )

            # Laser Dropdowns
            self.laser_variables.append(tk.StringVar())
            self.laser_pulldowns.append(
                ttk.Combobox(self, textvariable=self.laser_variables[num], width=6)
            )
            self.laser_pulldowns[num].config(state="readonly")
            self.laser_pulldowns[num].grid(
                row=num + 1,
                column=(column_id := column_id + 1),
                sticky=tk.NSEW,
                padx=self.pad_x,
                pady=self.pad_y,
            )

            # Laser Power Spinbox
            self.laserpower_variables.append(tk.StringVar())
            self.laserpower_pulldowns.append(
                ValidatedSpinbox(
                    self, textvariable=self.laserpower_variables[num], width=4
                )
            )
            self.laserpower_pulldowns[num].grid(
                row=num + 1,
                column=(column_id := column_id + 1),
                sticky=tk.NSEW,
                padx=self.pad_x,
                pady=self.pad_y,
            )

            # FilterWheel Dropdowns
            for i in range(filter_wheels):
                self.filterwheel_variables.append(tk.StringVar())
                self.filterwheel_pulldowns.append(
                    ttk.Combobox(
                        self, textvariable=self.filterwheel_variables[-1], width=10
                    )
                )
                self.filterwheel_pulldowns[-1].config(state="readonly")
                if self.should_hide_filter_wheel(
                    i, filter_wheel_types, filter_wheel_visibility
                ):
                    continue
                self.filterwheel_pulldowns[-1].grid(
                    row=num + 1,
                    column=(column_id := column_id + 1),
                    sticky=tk.NSEW,
                    padx=self.pad_x,
                    pady=self.pad_y,
                )

            # Exposure Time Spin boxes
            self.exptime_variables.append(tk.StringVar())
            self.exptime_pulldowns.append(
                ValidatedSpinbox(
                    self, textvariable=self.exptime_variables[num], width=7
                )
            )
            self.exptime_pulldowns[num].grid(
                row=num + 1,
                column=(column_id := column_id + 1),
                sticky=tk.NSEW,
                padx=self.pad_x,
                pady=self.pad_y,
            )

            # Time Interval Spin boxes
            self.interval_variables.append(tk.StringVar())
            self.interval_spins.append(
                ValidatedSpinbox(
                    self, textvariable=self.interval_variables[num], width=3
                )
            )
            self.interval_spins[num].grid(
                row=num + 1,
                column=(column_id := column_id + 1),
                sticky=tk.NSEW,
                padx=self.pad_x,
                pady=self.pad_y,
            )

            # Defocus Spinbox
            self.defocus_variables.append(tk.DoubleVar())
            self.defocus_spins.append(
                ValidatedSpinbox(
                    self,
                    textvariable=self.defocus_variables[num],
                    width=4,
                    from_=-100,
                    to=100,
                    increment=0.1,
                )
            )
            self.defocus_spins[num].grid(
                row=num + 1,
                column=(column_id := column_id + 1),
                sticky=tk.NSEW,
                padx=self.pad_x,
                pady=self.pad_y,
            )

    def create_labels(
        self,
        filter_wheel_names: list,
        filter_wheels: int,
        filter_wheel_types: list = None,
        filter_wheel_visibility: list = None,
    ) -> None:
        """Create the labels for the columns.

        Function to create the labels for the columns of the Channel Creator frame.

        Parameters
        ----------
        filter_wheel_names : list
            A list of the names of the filter wheels
        filter_wheels : int
            Number of filter wheels
        filter_wheel_types : list
            The types of filter wheels
        filter_wheel_visibility : list
            Indicates whether each filter wheel belongs to this microscope
        """
        # Create the labels for the columns.
        self.label_text = [
            "Channel",
            "Laser",
            "Power",
        ]
        for i in range(filter_wheels):
            if self.should_hide_filter_wheel(
                i, filter_wheel_types, filter_wheel_visibility
            ):
                continue
            self.label_text.append(filter_wheel_names[i])

        self.label_text += ["Exp. Time (ms)", "Interval", "Defocus"]

        for idx in range(len(self.label_text)):
            self.frame_columns.append(ttk.Frame(self))
            self.frame_columns[idx].grid(
                row=0, column=idx, sticky=tk.NSEW, padx=self.pad_x, pady=self.pad_y
            )
            self.labels.append(
                ttk.Label(self.frame_columns[idx], text=self.label_text[idx])
            )
            self.labels[idx].grid(
                row=0, column=0, sticky=tk.N, pady=self.pad_y, padx=self.pad_x
            )

    def reset_frame(self) -> None:
        """Destroy existing channel widgets and clear references."""
        for child in self.winfo_children():
            child.destroy()

        self.channel_variables = []
        self.channel_checks = []
        self.laser_variables = []
        self.laser_pulldowns = []
        self.laserpower_variables = []
        self.laserpower_pulldowns = []
        self.filterwheel_variables = []
        self.filterwheel_pulldowns = []
        self.exptime_variables = []
        self.exptime_pulldowns = []
        self.interval_variables = []
        self.interval_spins = []
        self.defocus_variables = []
        self.defocus_spins = []
        self.labels = []
        self.frame_columns = []

    @staticmethod
    def is_synthetic_filter_wheel(
        filter_wheel_idx: int, filter_wheel_types: list
    ) -> bool:
        """Return whether a filter wheel type should be hidden in the GUI."""
        if filter_wheel_types is None or filter_wheel_idx >= len(filter_wheel_types):
            return False

        filter_wheel_type = str(filter_wheel_types[filter_wheel_idx]).strip().lower()
        return filter_wheel_type in ("synthetic", "syntheticfilterwheel")

    @classmethod
    def should_hide_filter_wheel(
        cls,
        filter_wheel_idx: int,
        filter_wheel_types: list,
        filter_wheel_visibility: list,
    ) -> bool:
        """Return whether a filter wheel should be hidden in the GUI."""
        if (
            filter_wheel_visibility is not None
            and filter_wheel_idx < len(filter_wheel_visibility)
            and not filter_wheel_visibility[filter_wheel_idx]
        ):
            return True

        return cls.is_synthetic_filter_wheel(filter_wheel_idx, filter_wheel_types)


class StackAcquisitionFrame(ttk.Labelframe):
    """This class is the frame that holds the stack acquisition settings."""

    def __init__(self, settings_tab: ChannelsTab, *args: list, **kwargs: dict) -> None:
        """Initialization of the Stack Acquisition Frame

        Parameters
        ----------
        settings_tab : ChannelsTab
            The frame that holds the settings tab.
        *args : list
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """
        # Init Frame
        text_label = "Stack Acquisition Settings (" + "\N{GREEK SMALL LETTER MU}" + "m)"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        #: dict: Dictionary of the widgets in the frame
        self.inputs = {}

        #: dict: Dictionary of the buttons in the frame
        self.buttons = {}

        #: dict: Dictionary of variables in the frame
        self.additional_stack_setting_variables = {}

        self.stack_frame = ttk.Frame(self)
        self.additional_stack_frame = ttk.Frame(self)
        self.stack_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.additional_stack_frame.grid(row=1, column=0, sticky=tk.NSEW)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Start Pos Frame (Vertically oriented)
        start_names = ["start_position", "start_focus"]
        start_labels = ["Pos", "Foc"]

        #: ttk.Label: The label for the start position frame
        start_label = ttk.Label(self.stack_frame, text="Start")
        start_label.grid(row=0, column=0, sticky="S")
        for i in range(len(start_names)):
            self.inputs[start_names[i]] = LabelInput(
                parent=self.stack_frame,
                label=start_labels[i],
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(),
                input_args={"width": 6},
            )
            self.inputs[start_names[i]].grid(
                row=i + 1, column=0, sticky="N", pady=2, padx=(6, 0)
            )
            self.inputs[start_names[i]].label.grid(sticky="N")

        # Start button
        self.buttons["set_start"] = HoverButton(
            self.stack_frame, text="Set Start Pos/Foc"
        )
        self.buttons["set_start"].grid(row=3, column=0, sticky="N", pady=2, padx=(6, 0))

        # End Pos Frame (Vertically Oriented)
        end_names = ["end_position", "end_focus"]
        end_labels = ["Pos", "Foc"]

        #: ttk.Label: The label for the end position
        end_label = ttk.Label(self.stack_frame, text="End")
        end_label.grid(row=0, column=1, sticky="S")
        for i in range(len(end_names)):
            self.inputs[end_names[i]] = LabelInput(
                parent=self.stack_frame,
                label=end_labels[i],
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(),
                input_args={"width": 6},
            )
            self.inputs[end_names[i]].grid(
                row=i + 1, column=1, sticky="N", pady=2, padx=(6, 0)
            )
            self.inputs[end_names[i]].label.grid(sticky="N")

        # End Button
        self.buttons["set_end"] = HoverButton(self.stack_frame, text="Set End Pos/Foc")
        self.buttons["set_end"].grid(row=3, column=1, sticky="N", pady=2, padx=(6, 0))

        #: ttk.Label: The label for the step size
        step_size_label = ttk.Label(self.stack_frame, text="Step Size")
        step_size_label.grid(row=0, column=2, sticky="S")
        self.inputs["step_size"] = LabelInput(
            parent=self.stack_frame,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"width": 6},
        )
        self.inputs["step_size"].grid(row=1, column=2, sticky="N", padx=6)

        # Slice Frame (Vertically oriented)
        #: ttk.Label: The label to add empty space to the slice frame
        self.empty_label = ttk.Label(self.stack_frame, text=" ")
        self.empty_label.grid(row=0, column=3, sticky="N")
        self.inputs["number_z_steps"] = LabelInput(
            parent=self.stack_frame,
            label="Z Slices".ljust(20),
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"width": 6},
        )
        self.inputs["number_z_steps"].widget.configure(state="disabled")
        self.inputs["number_z_steps"].grid(
            row=1, column=3, sticky="NSEW", pady=2, padx=(6, 0)
        )

        # devices
        self.inputs["z_device"] = LabelInput(
            parent=self.stack_frame,
            label="Z-Stack Device".ljust(30),
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            input_args={"width": 8},
        )
        self.inputs["z_device"].state(["disabled", "readonly"])
        self.inputs["z_device"].grid(
            row=4, column=0, columnspan=2, sticky="NSEW", padx=6, pady=5
        )

        self.inputs["f_device"] = LabelInput(
            parent=self.stack_frame,
            label="Focus Device".ljust(30),
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            input_args={"width": 8},
        )
        self.inputs["f_device"].state(["disabled", "readonly"])
        self.inputs["f_device"].grid(
            row=5, column=0, columnspan=2, sticky="NSEW", padx=6, pady=5
        )

        # Laser Cycling Settings
        self.inputs["cycling"] = LabelInput(
            parent=self.stack_frame,
            label="Laser Cycling Settings".ljust(25),
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            input_args={"width": 8},
        )
        self.inputs["cycling"].state(["readonly"])
        self.inputs["cycling"].grid(
            row=6, column=0, columnspan=2, sticky="NSEW", padx=6, pady=5
        )

        self.inputs["speed"] = LabelInput(
            parent=self.stack_frame,
            label="Speed Mode".ljust(30),
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 8, "values": ["Auto", "Fixed"]},
        )
        self.inputs["speed"].state(["disabled", "readonly"])
        self.inputs["speed"].grid(
            row=7, column=0, columnspan=2, sticky="NSEW", padx=5, pady=5
        )

        self.cubic_frame = ttk.Frame(self.stack_frame)
        self.cubic_frame.grid(
            row=3,
            rowspan=3,
            column=2,
            columnspan=2,
            sticky=tk.NE,
            padx=(5, 15),
            pady=(5, 0),
        )

        image_directory = Path(__file__).resolve().parent

        self.image = tk.PhotoImage(
            file=image_directory.joinpath("images", "cubic_bottom_to_top.png")
        )

        # Use ttk.Label
        self.cubic_image_label = ttk.Label(self.cubic_frame, image=self.image)
        self.cubic_image_label.grid(
            row=0,
            rowspan=2,
            column=0,
            columnspan=2,
            sticky=tk.NSEW,
            padx=(5, 0),
            pady=(5, 0),
        )

        self.inputs["top"] = LabelInput(
            parent=self.cubic_frame,
            label="",
            input_class=ttk.Entry,
            input_var=tk.DoubleVar(),
            input_args={"width": 6},
        )
        self.inputs["top"].grid(row=0, column=2, sticky=tk.EW, padx=0, pady=(15, 0))
        self.inputs["top"].widget.configure(state="disabled")

        self.inputs["bottom"] = LabelInput(
            parent=self.cubic_frame,
            label="",
            input_class=ttk.Entry,
            input_var=tk.DoubleVar(),
            input_args={"width": 6},
        )
        self.inputs["bottom"].grid(row=1, column=2, sticky=tk.EW, padx=0, pady=(10, 0))
        self.inputs["bottom"].widget.configure(state="disabled")

        self.inputs["z_offset"] = LabelInput(
            parent=self.additional_stack_frame,
            label="Z Offset".ljust(30),
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"width": 8},
        )
        self.inputs["z_offset"].widget.configure(state="disabled")
        self.inputs["z_offset"].grid(
            row=0, column=0, columnspan=2, sticky="NSEW", padx=6, pady=5
        )

        uniform_grid(self)

        # Initialize DescriptionHovers
        self.inputs["step_size"].widget.hover.setdescription("The Z-stack step size.")
        self.inputs["cycling"].widget.hover.setdescription(
            "Per Stack - Captures a full z-stack for each channel in sequence, \n"
            "scanning from the start to end Z positions for one channel before \n"
            "moving on to the next. \n\n"
            "Per Channel - Captures the full z-stack in an interleaved fashion, \n"
            "acquiring every channel at each z-plane before moving to the next."
        )
        self.inputs["z_offset"].widget.hover.setdescription(
            "The relative offset between the Z stages, if applicable."
        )
        self.buttons["set_end"].hover.setdescription(
            "Sets the Z-stack end position for the F and Z Axes."
        )
        self.buttons["set_start"].hover.setdescription(
            "Sets the Z-stack start position for the F and Z Axes."
        )
        self.inputs["z_device"].widget.hover.setdescription(
            "The device that controls the Z-stack."
        )
        self.inputs["start_position"].widget.hover.setdescription(
            "The relative starting Z position for the Z-stack."
        )
        self.inputs["start_focus"].widget.hover.setdescription(
            "The relative starting F position for the Z-stack."
        )
        self.inputs["end_position"].widget.hover.setdescription(
            "The relative ending Z position for the Z-stack."
        )
        self.inputs["end_focus"].widget.hover.setdescription(
            "The relative ending F position for the Z-stack."
        )
        self.inputs["number_z_steps"].widget.hover.setdescription(
            "The number of Z slices in the Z stack per channel."
        )
        # self.inputs["abs_z_start"].widget.hover.setdescription(
        #     "The absolute Z start position for the Z-stack."
        # )
        # self.inputs["abs_z_end"].widget.hover.setdescription(
        #     "The absolute Z end position for the Z-stack."
        # )

    def create_additional_stack_widgets(self, axes: list, devices: dict) -> None:
        """Create the additional stack widgets.

        This function creates the additional stack widgets for the
        stack acquisition settings.

        Parameters
        ----------
        axes : list
            The list of axes to create the widgets for.
        devices : dict
            The dictionary of devices to create the widgets for. {axis: device_name}
        """
        # Create the additional stack widgets here
        for widget in self.additional_stack_frame.winfo_children():
            widget.destroy()
        self.additional_stack_setting_variables = {}
        self.selected_axes_num = 0

        if len(axes) <= 2:
            return

        self.devices_dict = devices

        # Create the additional stack widgets here
        separator = ttk.Separator(self.additional_stack_frame, orient=tk.HORIZONTAL)
        separator.grid(row=0, column=0, columnspan=10, sticky=tk.NSEW, pady=(5, 0))

        # Stacking on axes
        label = ttk.Label(self.additional_stack_frame, text="Stacking on axes:")
        label.grid(row=1, column=0, sticky=tk.NSEW, padx=(5, 30), pady=(5, 0))

        for axis in axes:
            self.additional_stack_setting_variables[f"stack_{axis}"] = tk.BooleanVar()
            self.inputs[f"stack_{axis}"] = ttk.Checkbutton(
                self.additional_stack_frame,
                text=axis.upper(),
                command=self.update_setting_widgets(axis),
                variable=self.additional_stack_setting_variables[f"stack_{axis}"],
            )
            self.inputs[f"stack_{axis}"].grid(
                row=1,
                column=axes.index(axis) + 1,
                sticky=tk.NW,
                padx=(5, 10),
                pady=(5, 0),
            )

        self.additional_stack_setting_frame = ttk.Frame(self.additional_stack_frame)
        self.additional_stack_setting_frame.grid(
            row=2, column=0, columnspan=10, sticky=tk.NSEW, padx=(5, 30), pady=(5, 0)
        )
        self.additional_stack_setting_labels = {}

        for i, label_text in enumerate(
            ["Axis", "Device", "Offset (" + "\N{GREEK SMALL LETTER MU}" + "m)"]
        ):  # , "Step", "Slice Num"]):
            label = ttk.Label(self.additional_stack_setting_frame, text=label_text)
            label.grid(row=0, column=i, sticky=tk.NSEW, padx=10, pady=2)
        for i, axis in enumerate(axes):
            label = ttk.Label(self.additional_stack_setting_frame, text=axis.upper())
            label.grid(row=i + 1, column=0, sticky=tk.NSEW, padx=10, pady=2)
            label.grid_remove()
            self.additional_stack_setting_labels[axis] = label
            # Create the device label
            label = ttk.Label(
                self.additional_stack_setting_frame, text=self.devices_dict[axis]
            )
            label.grid(row=i + 1, column=1, sticky=tk.NSEW, padx=10, pady=2)
            label.grid_remove()
            self.additional_stack_setting_labels[f"{axis}_device"] = label
            # Create the offset spinbox
            index_name = f"{axis}_offset"
            self.additional_stack_setting_variables[index_name] = tk.DoubleVar()
            self.inputs[index_name] = ValidatedSpinbox(
                master=self.additional_stack_setting_frame,
                from_=-10000,
                to=10000,
                textvariable=self.additional_stack_setting_variables[index_name],
            )
            self.inputs[index_name].grid(
                row=i + 1, column=2, sticky=tk.NSEW, padx=10, pady=2
            )
            self.inputs[index_name].grid_remove()

        self.additional_stack_setting_frame.grid_remove()

        uniform_grid(self.additional_stack_frame)

    def update_setting_widgets(self, axis: str) -> None:
        """Update the setting widgets based on the movement mode.

        This function updates the setting widgets based on the
        movement mode selected.

        Parameters
        ----------
        axis : str
            The axis to update the widgets for.
        """

        def func(*args: list) -> None:
            """Inner function to update the widgets.

            Parameters
            ----------
            *args : list
                The arguments passed to the function.
            """
            if self.additional_stack_setting_variables[f"stack_{axis}"].get():
                self.additional_stack_setting_frame.grid()
                self.inputs[f"{axis}_offset"].grid()
                self.additional_stack_setting_labels[axis].grid()
                self.additional_stack_setting_labels[f"{axis}_device"].grid()
                self.selected_axes_num += 1
            else:
                self.inputs[f"{axis}_offset"].grid_remove()
                self.additional_stack_setting_labels[axis].grid_remove()
                self.additional_stack_setting_labels[f"{axis}_device"].grid_remove()
                self.selected_axes_num -= 1
                if self.selected_axes_num <= 0:
                    self.additional_stack_setting_frame.grid_remove()

        return func

    # Getters
    def get_variables(self) -> dict:
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

    def get_widgets(self) -> dict:
        """Returns a dictionary of the widgets.

        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        dict
            Dictionary of the widgets in the widget
        """
        return self.inputs

    def get_buttons(self) -> dict:
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
    """Frame for the stack time point settings in the channels tab.

    This class is a frame that holds the widgets for the stack time point settings.
    It is a subclass of ttk.Labelframe.
    """

    def __init__(self, settings_tab: ChannelsTab, *args: list, **kwargs: dict) -> None:
        """Initialization of the Stack Time point Frame

        Parameters
        ----------
        settings_tab : ChannelsTab
            The frame that the stack time point frame will be placed in
        *args : list
            Variable length argument list
        **kwargs : dict
            Arbitrary keyword arguments
        """
        text_label = "Timepoint Settings"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        #: dict: Dictionary of the widgets in the frame
        self.inputs = {}

        #: ttk.Label: The label for the save data checkbox
        self.laser_label = ttk.Label(self, text="Save Data")
        self.laser_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(4, 5), pady=(4, 0))

        #: tk.BooleanVar: The variable for the save data checkbox
        self.save_data = tk.BooleanVar()
        self.save_data.set(False)

        #: ttk.Checkbutton: The save data checkbox
        self.save_check = ttk.Checkbutton(self, text="", variable=self.save_data)
        self.save_check.grid(row=0, column=1, sticky=tk.NSEW, pady=(4, 0))
        self.inputs["save_check"] = self.save_check

        #: ttk.Label: The label for the timepoints spinbox
        self.filterwheel_label = ttk.Label(self, text="Timepoints")
        self.filterwheel_label.grid(
            row=1, column=0, sticky=tk.NSEW, padx=(4, 5), pady=2
        )

        #: tk.StringVar: The variable for the timepoints spinbox
        self.exp_time_spinval = tk.StringVar()

        #: ValidatedSpinbox: The timepoints spinbox
        self.exp_time_spinbox = ValidatedSpinbox(
            self, textvariable=self.exp_time_spinval, width=3
        )
        self.exp_time_spinbox.grid(row=1, column=1, sticky=tk.NSEW, pady=2)
        self.inputs["time_spin"] = self.exp_time_spinbox

        #: ttk.Label: The label for the stack acquisition time spinbox
        self.exp_time_label = ttk.Label(self, text="Stack Acq. Time")
        self.exp_time_label.grid(row=2, column=0, sticky=tk.NSEW, padx=(4, 5), pady=2)

        #: tk.StringVar: The variable for the stack acquisition time spinbox
        self.stack_acq_spinval = tk.StringVar()

        #: ttk.Spinbox: The stack acquisition time spinbox
        self.stack_acq_spinbox = ttk.Spinbox(
            self, textvariable=self.stack_acq_spinval, width=6
        )
        self.stack_acq_spinbox.grid(row=2, column=1, sticky=tk.NSEW, pady=2)
        self.stack_acq_spinbox.state(["disabled"])

        #: ttk.Label: The label for the stack pause spinbox
        self.exp_time_label = ttk.Label(self, text="Stack Pause (s)")
        self.exp_time_label.grid(row=0, column=2, sticky=tk.NSEW, padx=(4, 5), pady=2)

        #: tk.StringVar: The variable for the stack pause spinbox
        self.stack_pause_spinval = tk.StringVar()

        #: ValidatedSpinbox: The stack pause spinbox
        self.stack_pause_spinbox = ValidatedSpinbox(
            self, textvariable=self.stack_pause_spinval, width=6
        )
        self.stack_pause_spinbox.grid(row=0, column=3, sticky=tk.NSEW, pady=2)
        self.inputs["stack_pause"] = self.stack_pause_spinbox

        #: ttk.Label: The label for the time point interval spinbox
        self.exp_time_label = ttk.Label(self, text="Time Interval (hh:mm:ss)")
        self.exp_time_label.grid(row=1, column=2, sticky=tk.NSEW, padx=(4, 5), pady=2)

        #: tk.StringVar: The variable for the time point interval spinbox
        self.timepoint_interval_spinval = tk.StringVar()
        if self.timepoint_interval_spinval.get() == "":
            self.timepoint_interval_spinval.set("0")

        #: ttk.Spinbox: The time point interval spinbox
        self.timepoint_interval_spinbox = ttk.Spinbox(
            self, textvariable=self.timepoint_interval_spinval, width=6
        )
        self.timepoint_interval_spinbox.grid(row=1, column=3, sticky=tk.NSEW, pady=2)
        self.timepoint_interval_spinbox.state(["disabled"])  # Starts it disabled

        #: ttk.Label: The label for the total time spinbox
        self.exp_time_label = ttk.Label(self, text="Experiment Duration (hh:mm:ss)")
        self.exp_time_label.grid(
            row=2, column=2, sticky=tk.NSEW, padx=(4, 5), pady=(2, 6)
        )

        #: tk.StringVar: The variable for the total time spinbox
        self.total_time_spinval = tk.StringVar()
        if self.total_time_spinval.get() == "":
            self.total_time_spinval.set("0")

        #: ttk.Spinbox: The total time spinbox
        self.total_time_spinval = ttk.Spinbox(
            self, textvariable=self.total_time_spinval, width=6
        )
        self.total_time_spinval.grid(row=2, column=3, sticky=tk.NSEW, pady=(2, 6))
        self.total_time_spinval.state(["disabled"])

    def get_variables(self) -> dict:
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

    def get_widgets(self) -> dict:
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

    def __init__(self, settings_tab: ChannelsTab, *args: list, **kwargs: dict) -> None:
        """Initialization of the Multi-Position Acquisition Frame

        Parameters
        ----------
        settings_tab : ChannelsTab
            The frame that the multipoint frame will be placed in
        *args : list
            Variable length argument list
        **kwargs : dict
            Arbitrary keyword arguments
        """
        text_label = "Multi-Position Acquisition"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        #: ttk.Label: The label for the save data checkbox
        self.laser_label = ttk.Label(self, text="Enable")
        self.laser_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(4, 4), pady=(4, 4))

        #: tk.BooleanVar: The variable for the save data checkbox
        self.on_off = tk.BooleanVar()

        #: ttk.Checkbutton: The save data checkbox
        self.save_check = ttk.Checkbutton(self, text="", variable=self.on_off)
        self.save_check.grid(row=0, column=1, sticky=tk.NSEW, pady=(4, 4))

        #: dict: Dictionary of the buttons in the frame
        self.buttons = {"tiling": ttk.Button(self, text="Launch Tiling Wizard")}
        self.buttons["tiling"].grid(
            row=0, column=2, sticky=tk.NSEW, padx=(10, 0), pady=(4, 4)
        )


class QuickLaunchFrame(ttk.Labelframe):
    """Quick Launch Buttons Frame

    This frame contains buttons that launch the Tiling Wizard.
    """

    def __init__(self, settings_tab: ChannelsTab, *args: list, **kwargs: dict) -> None:
        """Initialization of the Quick Launch Buttons Frame

        Parameters
        ----------
        settings_tab : ChannelsTab
            The settings tab object that this frame is being added to.
        *args : list
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """
        text_label = "Quick Launch Buttons"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        #: Dict[str, ttk.Button]: Dictionary of the buttons in the frame
        self.buttons: Dict[str, ttk.Button] = {}
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
