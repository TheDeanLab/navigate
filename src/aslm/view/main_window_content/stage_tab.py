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
from tkinter import ttk, Grid
import logging
from pathlib import Path

# Third Party Imports

# Local Imports
from aslm.view.custom_widgets.hovermixin import HoverButton, HoverTkButton
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.validation import ValidatedSpinbox
from aslm.view.custom_widgets.validation import ValidatedEntry


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class StageControlNotebook(ttk.Notebook):
    """Notebook for stage control tab.

    Parameters
    ----------
    frame_bot_right : tk.Frame
        Frame to put notebook into.
    *args
        Arguments for ttk.Notebook
    **kwargs
        Keyword arguments for ttk.Notebook

    Attributes
    ----------
    stage_control_tab : StageControlTab
        Stage control tab.
    maximum_intensity_projection_tab : MaximumIntensityProjectionTab
        Maximum intensity projection tab.

    Methods
    -------
    None
    """

    def __init__(self, frame_bot_right, *args, **kwargs):
        # Init notebook
        ttk.Notebook.__init__(self, frame_bot_right, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Putting notebook 3 into bottom right frame
        self.grid(row=0, column=0)

        # Creating Stage Control Tab
        self.stage_control_tab = StageControlTab(self)

        # Adding tabs to notebook
        self.add(self.stage_control_tab, text="Stage Control", sticky=tk.NSEW)


class GoToFrame(ttk.Frame):
    """GoTo Frame for stage control tab.

    Parameters
    ----------
    stage_control_tab : StageControlTab
        Stage control tab.
    *args
        Arguments for ttk.Frame
    **kwargs
        Keyword arguments for ttk.Frame

    Attributes
    ----------
    None

    Methods
    -------
    None
    """

    def __init__(goto_frame, stage_control_tab, *args, **kwargs):
        # Init Frame
        ttk.Frame.__init__(goto_frame, stage_control_tab, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(goto_frame, "all", weight=1)
        tk.Grid.rowconfigure(goto_frame, "all", weight=1)


class StageControlTab(tk.Frame):
    """Stage Control Tab for stage control notebook.

    Parameters
    ----------
    note3 : ttk.Notebook
        Stage control notebook.
    *args
        Arguments for tk.Frame
    **kwargs
        Keyword arguments for tk.Frame

    Attributes
    ----------
    index : int
        Index of tab in notebook.
    position_frame : PositionFrame
        Position frame.
    xy_frame : XYFrame
        XY frame.
    z_frame : OtherAxisFrame
        Z frame.
    theta_frame : OtherAxisFrame
        Theta frame.
    f_frame : OtherAxisFrame
        Focus frame.
    goto_frame : GoToFrame
        GoTo frame.

    Methods
    -------
    None
    """

    def __init__(self, note3, *args, **kwargs):
        # Init Frame
        tk.Frame.__init__(self, note3, *args, **kwargs)

        self.index = 2

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Building out stage control elements, frame by frame

        # Position Frame
        self.position_frame = PositionFrame(self)

        # XY Frame
        self.xy_frame = XYFrame(self)

        # Z Frame
        self.z_frame = OtherAxisFrame(self, "Z")

        # Theta Frame
        self.theta_frame = OtherAxisFrame(self, "Theta")

        # Focus Frame
        self.f_frame = OtherAxisFrame(self, "Focus")

        # GoTo Frame
        self.goto_frame = GoToFrame(self)
        self.goto_frame_label = ttk.Label(self.goto_frame, text="Goto Frame")
        self.goto_frame_label.pack()  # For visual mockup purposes

        # stop frame
        self.stop_frame = StopFrame(self, "Stop")

        """
        Grid for frames
                1   2   3   4   5
                6   7   8   9   10

        Position frame is 1-5
        xy is 6
        z is 7
        theta is 8
        focus is 9
        goto is 10
        """

        # Formatting
        tk.Grid.columnconfigure(self.position_frame, "all", weight=1)
        tk.Grid.rowconfigure(self.position_frame, "all", weight=1)
        tk.Grid.columnconfigure(self.xy_frame, "all", weight=1)
        tk.Grid.rowconfigure(self.xy_frame, "all", weight=1)
        tk.Grid.columnconfigure(self.z_frame, "all", weight=1)
        tk.Grid.rowconfigure(self.z_frame, "all", weight=1)
        tk.Grid.columnconfigure(self.theta_frame, "all", weight=1)
        tk.Grid.rowconfigure(self.theta_frame, "all", weight=1)
        tk.Grid.columnconfigure(self.f_frame, "all", weight=1)
        tk.Grid.rowconfigure(self.f_frame, "all", weight=1)
        tk.Grid.columnconfigure(self.goto_frame, "all", weight=1)
        tk.Grid.rowconfigure(self.goto_frame, "all", weight=1)
        tk.Grid.columnconfigure(self.stop_frame, "all", weight=1)
        tk.Grid.rowconfigure(self.stop_frame, "all", weight=1)

        # Gridding out frames
        self.position_frame.grid(row=0, column=0, sticky=(tk.NSEW), padx=3, pady=3)
        self.xy_frame.grid(row=0, column=1, sticky=(tk.NSEW), padx=3, pady=3)
        self.z_frame.grid(row=0, column=2, sticky=(tk.NSEW), padx=3, pady=3)
        self.f_frame.grid(row=1, column=0, sticky=(tk.NSEW), padx=3, pady=3)
        self.theta_frame.grid(row=1, column=2, sticky=(tk.NSEW), padx=3, pady=3)
        # self.goto_frame.grid(row=0, column=4, sticky=(tk.NSEW))
        self.stop_frame.grid(row=1, column=1, sticky=(tk.NSEW), padx=3, pady=3)

        # example hover description
        self.xy_frame.up_y_btn.hover.setdescription(
            "Increases the Y value of the stage's position"
        )
        self.xy_frame.down_y_btn.hover.setdescription(
            "Decreases the Y value of the stage's position"
        )
        self.xy_frame.down_x_btn.hover.setdescription(
            "Decreases the X value of the stage's position"
        )
        self.xy_frame.up_x_btn.hover.setdescription(
            "Increases the X value of the stage's position"
        )
        self.position_frame.inputs["y"].widget.hover.setdescription(
            "Y position of the stage"
        )
        self.position_frame.inputs["x"].widget.hover.setdescription(
            "X position of the stage"
        )
        self.position_frame.inputs["z"].widget.hover.setdescription(
            "Z position of the stage"
        )
        self.position_frame.inputs["f"].widget.hover.setdescription(
            "Focus"
        )
        self.stop_frame.joystick_btn.hover.setdescription(
            "Enables/disables joystick mode"
        )

    def get_widgets(self):
        """Get all widgets in the stage control tab.

        This function will return all the input widgets as a dictionary
        The reference name in the dictionary is the same as in the widget list file

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of widgets
        """
        temp = {**self.position_frame.get_widgets()}
        for axis in ["xy", "z", "theta", "f"]:
            temp[axis + "_step"] = getattr(self, axis + "_frame").get_widget()
        return temp

    def get_variables(self):
        """Get all variables in the stage control tab.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of variables
        """
        temp = self.get_widgets()
        return {k: temp[k].get_variable() for k in temp}

    def get_buttons(self):
        """Get all buttons in the stage control tab.

        this function returns all the buttons in a dictionary
        the reference name is the same as in widget list

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of buttons
        """
        result = {**self.xy_frame.get_buttons()}
        for axis in ["z", "theta", "f"]:
            temp = getattr(self, axis + "_frame").get_buttons()
            result.update({k + "_" + axis + "_btn": temp[k] for k in temp})
        result.update(self.stop_frame.get_buttons())
        return result

    def toggle_button_states(self, joystick_is_on = False, joystick_axes = []):
        
        self.xy_frame.toggle_button_states(joystick_is_on, joystick_axes)
        self.z_frame.toggle_button_states(joystick_is_on, joystick_axes)
        self.f_frame.toggle_button_states(joystick_is_on, joystick_axes)
        self.theta_frame.toggle_button_states(joystick_is_on, joystick_axes)
        self.position_frame.toggle_entry_states(joystick_is_on, joystick_axes)
        self.stop_frame.toggle_button_states(joystick_is_on, joystick_axes)

class OtherAxisFrame(ttk.Labelframe):
    """Frame for the other axis movement buttons.

    This frame is used for the z, theta, and focus axis movement buttons.

    Parameters
    ----------
    other_axis_frame : tk.Frame
        The frame to be used for the other axis movement buttons
    stage_control_tab : tk.Frame
        The stage control tab that the other axis frame is in
    name : str
        The name of the axis that the frame is for
    *args : tuple
        Positional arguments for the ttk.Labelframe
    **kwargs : dict
        Keyword arguments for the ttk.Labelframe

    Attributes
    ----------
    name : str
        The name of the axis that the frame is for
    up_image : tk.PhotoImage
        The image for the up button
    down_image : tk.PhotoImage
        The image for the down button

    Methods
    -------
    get_widgets()
        Get all widgets in the other axis frame
    get_buttons()
        Get all buttons in the other axis frame
    """

    def __init__(other_axis_frame, stage_control_tab, name, *args, **kwargs):
        # Init Frame
        label = name
        ttk.Labelframe.__init__(
            other_axis_frame,
            stage_control_tab,
            text=label + " Movement",
            *args,
            **kwargs
        )
        other_axis_frame.name = name

        # Formatting
        tk.Grid.columnconfigure(other_axis_frame, "all", weight=1)
        tk.Grid.rowconfigure(other_axis_frame, "all", weight=1)

        image_directory = Path(__file__).resolve().parent
        other_axis_frame.up_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyup.png")
        )
        other_axis_frame.down_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greydown.png")
        )

        other_axis_frame.d_up_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyup_disabled.png")
        )
        other_axis_frame.d_down_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greydown_disabled.png")
        )

        other_axis_frame.up_image = other_axis_frame.up_image.subsample(2, 2)
        other_axis_frame.down_image = other_axis_frame.down_image.subsample(2, 2)

        other_axis_frame.normal_images = [other_axis_frame.up_image,
                                           other_axis_frame.down_image
                                           ]

        other_axis_frame.d_up_image = other_axis_frame.d_up_image.subsample(2, 2)
        other_axis_frame.d_down_image = other_axis_frame.d_down_image.subsample(2, 2)

        other_axis_frame.disabled_images = [other_axis_frame.d_up_image,
                                           other_axis_frame.d_down_image
                                           ]
        
        # Setting up buttons for up, down, zero and increment spinbox

        # Up button
        other_axis_frame.up_btn = HoverTkButton(
            other_axis_frame, image=other_axis_frame.up_image, borderwidth=0
        )

        # Down button
        other_axis_frame.down_btn = HoverTkButton(
            other_axis_frame, image=other_axis_frame.down_image, borderwidth=0
        )

        # Zero button
        other_axis_frame.zero_btn = HoverTkButton(
            other_axis_frame,
            text="ZERO " + other_axis_frame.name,
        )

        # Increment spinbox
        other_axis_frame.increment_box = LabelInput(
            parent=other_axis_frame,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"width": 5},
        )

        """
        Grid for buttons

                1
                2
                3
                4
                5
                6

        Up is 1,2
        Down is 5,6
        Increment is 3
        Zero is 4
        """

        # Button hover text
        other_axis_frame.hover_text_ending = ""
        if other_axis_frame.name == "Z":
            other_axis_frame.hover_text_ending = f"the {other_axis_frame.name} value of the stage's position"
        elif other_axis_frame.name == "Theta":
            other_axis_frame.hover_text_ending = f"the angle of sample rotation"
        else:
            other_axis_frame.hover_text_ending = f"the {other_axis_frame.name.lower()}"
            
        other_axis_frame.up_btn.hover.setdescription(
            f"Increases {other_axis_frame.hover_text_ending}"
        )
        other_axis_frame.down_btn.hover.setdescription(
            f"Decreases {other_axis_frame.hover_text_ending}"
        )
        other_axis_frame.normal_hover_texts = [other_axis_frame.up_btn.hover.getdescription(),
                                                other_axis_frame.down_btn.hover.getdescription()
                                                ]

        other_axis_frame.disabled_hover_texts = ["Turn off Joystick Mode to enable",
                                                 "Turn off Joystick Mode to enable"
                                                 ]
        
        # Gridding out buttons
        other_axis_frame.up_btn.grid(row=0, column=0, pady=2)  # UP
        other_axis_frame.down_btn.grid(row=3, column=0, pady=2)  # DOWN
        other_axis_frame.increment_box.grid(row=2, column=0, pady=2)
        other_axis_frame.increment_box.widget.set_precision(-1)     

    def get_widget(other_axis_frame):
        return other_axis_frame.increment_box

    def get_buttons(other_axis_frame):
        return {
            "up": other_axis_frame.up_btn,
            "down": other_axis_frame.down_btn,
            "zero": other_axis_frame.zero_btn,
        }
    
    def toggle_button_states(other_axis_frame, joystick_is_on = False, joystick_axes = []):
        """Switches the images used as buttons between two states

        Parameters
        ----------
        other_axis_frame : OtherAxisFrame
            The OtherAxisFrame object

        """
        if (other_axis_frame.name.lower() in joystick_axes) or (
            other_axis_frame.name.lower() == "focus" and "f" in joystick_axes):

            buttons = [other_axis_frame.up_btn,other_axis_frame.down_btn]
            if joystick_is_on:
                button_state = "disabled"
                image_list = other_axis_frame.disabled_images
                hover_list = other_axis_frame.disabled_hover_texts
            else:
                button_state = "normal"
                image_list = other_axis_frame.normal_images
                hover_list = other_axis_frame.normal_hover_texts
            for k in range(len(buttons)):
                    buttons[k]['state'] = button_state
                    buttons[k].config(image = image_list[k])
                    buttons[k].hover.setdescription(hover_list[k])


class PositionFrame(ttk.Labelframe):
    """Frame for the stage position entries.

    This frame is used for the x, y, z, theta, and focus position entries.

    Parameters
    ----------
    position_frame : tk.Frame
        The frame to be used for the stage position entries
    stage_control_tab : tk.Frame
        The stage control tab that the position frame is in
    *args : tuple
        Positional arguments for the ttk.Labelframe
    **kwargs : dict
        Keyword arguments for the ttk.Labelframe

    Attributes
    ----------
    inputs : dict
        A dictionary of the label input widgets for the position entries

    Methods
    -------
    get_widgets()
        Get all widgets in the position frame
    get_variables()
        Get all variables in the position frame
    """

    def __init__(position_frame, stage_control_tab, *args, **kwargs):

        # Init Frame
        ttk.Labelframe.__init__(
            position_frame, stage_control_tab, text="Stage Positions", *args, **kwargs
        )

        # Formatting
        tk.Grid.columnconfigure(position_frame, "all", weight=1)
        tk.Grid.rowconfigure(position_frame, "all", weight=1)

        # Creating each entry frame for a label and entry
        position_frame.inputs = {}
        entry_names = ["x", "y", "z", "theta", "f"]
        entry_labels = ["X", "Y", "Z", "\N{Greek Capital Theta Symbol}", "F"]

        # entries
        position_frame.frame_back_list = []
        for i in range(len(entry_names)):
            position_frame.inputs[entry_names[i]] = LabelInput(
                parent=position_frame,
                label=entry_labels[i],
                input_class=ValidatedEntry,
                input_var=tk.DoubleVar(),
                input_args={
                    "required": True,
                    "precision": 0.1,
                    "width": 6,
                    "takefocus": False,
                },
            )
            position_frame.frame_back_list.append(tk.Frame(position_frame,bg="#f0f0f0",width=60,height=26))
            position_frame.frame_back_list[i].grid(row=i,column=0)
            position_frame.inputs[entry_names[i]].grid(row=i, column=0)
            position_frame.frame_back_list[i].lower()

        """
        Grid for frames

                1
                2
                3
                4
                5

        x is 1
        y is 2
        z is 3
        theta is 4
        focus is 5
        """

    def get_widgets(position_frame):
        """Get all widgets in the position frame

        Parameters
        ----------
        position_frame : tk.Frame
            The frame to be used for the stage position entries

        Returns
        -------
        dict
            A dictionary of the label input widgets for the position entries
        """
        return position_frame.inputs

    def get_variables(position_frame):
        """Get all variables in the position frame

        Parameters
        ----------
        position_frame : tk.Frame
            The frame to be used for the stage position entries

        Returns
        -------
        dict
            A dictionary of the variables for the position entries
        """
        variables = {}
        for name in position_frame.inputs:
            variables[name] = position_frame.inputs[name].get_variable()
        return variables

    def toggle_entry_states(position_frame, joystick_is_on = False, joystick_axes = []):
        """Switches the images used as buttons between two states

        Parameters
        ----------
        x_y_frame : XYFrame
            The XYFrame object

        """
        frame_back_counter = 0
        if joystick_is_on:
            entry_state = "disabled"
            frame_back_color = "#ee868a"
        else:
            entry_state = "normal"
            frame_back_color = "#f0f0f0"
        
        for variable in position_frame.get_variables():
            if variable in joystick_axes:
                position_frame.frame_back_list[frame_back_counter]['bg'] = frame_back_color
                try:
                    position_frame.inputs[f'{variable}'].widget['state'] = entry_state

                except KeyError:
                    pass
            frame_back_counter += 1

class XYFrame(ttk.Labelframe):
    """Frame for the x and y movement buttons.

    This frame is used for the up, down, left, right, zero, and increment buttons.

    Parameters
    ----------
    x_y_frame : tk.Frame
        The frame to be used for the x and y movement buttons
    stage_control_tab : tk.Frame
        The stage control tab that the x y frame is in
    *args : tuple
        Positional arguments for the ttk.Labelframe
    **kwargs : dict
        Keyword arguments for the ttk.Labelframe

    Attributes
    ----------
    up_btn : tk.Button
        The button for moving up
    down_btn : tk.Button
        The button for moving down
    left_btn : tk.Button
        The button for moving left
    right_btn : tk.Button
        The button for moving right
    zero_btn : tk.Button
        The button for zeroing the x and y positions
    increment_box : tk.Spinbox
        The spinbox for the increment value

    Methods
    -------
    get_buttons()
        Get all buttons in the x y frame
    get_widget()
        Get the increment widget in the x y frame
    """

    def __init__(x_y_frame, stage_control_tab, *args, **kwargs):
        # Init Frame
        ttk.Labelframe.__init__(
            x_y_frame, stage_control_tab, text="X Y Movement", *args, **kwargs
        )

        # Formatting
        Grid.columnconfigure(x_y_frame, "all", weight=1)
        Grid.rowconfigure(x_y_frame, "all", weight=1)

        # Setting up buttons for up, down, left, right, zero and increment spinbox
        s = ttk.Style()
        s.configure("arrow.TButton", font=(None, 20))

        # Path to arrows
        image_directory = Path(__file__).resolve().parent
        
        x_y_frame.up_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyup.png")
        )
        x_y_frame.down_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greydown.png")
        )
        x_y_frame.left_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyleft.png")
        )
        x_y_frame.right_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyright.png")
        )
        x_y_frame.d_up_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyup_disabled.png")
        )
        x_y_frame.d_down_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greydown_disabled.png")
        )
        x_y_frame.d_left_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyleft_disabled.png")
        )
        x_y_frame.d_right_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "greyright_disabled.png")
        )
        x_y_frame.right_image = x_y_frame.right_image.subsample(2, 2)
        x_y_frame.left_image = x_y_frame.left_image.subsample(2, 2)
        x_y_frame.up_image = x_y_frame.up_image.subsample(2, 2)
        x_y_frame.down_image = x_y_frame.down_image.subsample(2, 2)

        x_y_frame.normal_images = [x_y_frame.right_image,
                                    x_y_frame.left_image,
                                    x_y_frame.up_image,
                                    x_y_frame.down_image]

        x_y_frame.normal_hover_texts = ["Decreases the X value of the stage's position",
                                               "Increases the X value of the stage's position",
                                               "Increases the Y value of the stage's position",
                                               "Decreases the Y value of the stage's position"
                                               ]
        
        x_y_frame.d_right_image = x_y_frame.d_right_image.subsample(2, 2)
        x_y_frame.d_left_image = x_y_frame.d_left_image.subsample(2, 2)
        x_y_frame.d_up_image = x_y_frame.d_up_image.subsample(2, 2)
        x_y_frame.d_down_image = x_y_frame.d_down_image.subsample(2, 2)

        x_y_frame.disabled_images = [x_y_frame.d_right_image,
                                     x_y_frame.d_left_image,
                                     x_y_frame.d_up_image,
                                     x_y_frame.d_down_image]
        
        x_y_frame.disabled_hover_texts = ["Turn off Joystick Mode to enable",
                                               "Turn off Joystick Mode to enable",
                                               "Turn off Joystick Mode to enable",
                                               "Turn off Joystick Mode to enable"
                                               ]



        # Up button
        x_y_frame.up_y_btn = HoverTkButton(
            x_y_frame,
            image=x_y_frame.up_image,
            borderwidth=0
            # style='arrow.TButton',
            # width=5
            # text="\N{UPWARDS BLACK ARROW}"
        )
        # Down button
        x_y_frame.down_y_btn = HoverTkButton(
            x_y_frame,
            image=x_y_frame.down_image,
            borderwidth=0
            # style='arrow.TButton',
            # width=10,
            # text="\N{DOWNWARDS BLACK ARROW}"
        )

        # Right button
        x_y_frame.up_x_btn = HoverTkButton(
            x_y_frame,
            image=x_y_frame.right_image,
            borderwidth=0
            # style='arrow.TButton',
            # width=10,
            # text="\N{RIGHTWARDS BLACK ARROW}"
        )

        # Left button
        x_y_frame.down_x_btn = HoverTkButton(
            x_y_frame,
            image=x_y_frame.left_image,
            borderwidth=0
            # style='arrow.TButton',
            # width=10,
            # text="\N{LEFTWARDS BLACK ARROW}"
        )

        # Zero button
        x_y_frame.zero_xy_btn = HoverTkButton(x_y_frame, text="ZERO XY")

        # Increment spinbox
        x_y_frame.increment_box = LabelInput(
            parent=x_y_frame,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={"width": 5},
        )
        x_y_frame.button_axes_dict = {'x':[x_y_frame.up_x_btn,x_y_frame.down_x_btn],
                                      'y':[x_y_frame.up_y_btn,x_y_frame.down_y_btn]}
        """
        Grid for buttons

                01  02  03  04  05  06
                07  08  09  10  11  12
                13  14  15  16  17  18
                19  20  21  22  23  24
                25  26  27  28  29  30
                31  32  33  34  35  36

        Up is 03,04,09,10
        Right is 17,18,23,24
        Down is 27,28,33,34
        Left is 13,14,19,20
        Increment is 15,16
        Zero XY is 21,22
        """

        # Gridding out buttons
        x_y_frame.up_y_btn.grid(
            row=0, column=2, rowspan=2, columnspan=2, padx=2, pady=2
        )  # UP
        x_y_frame.up_x_btn.grid(
            row=2, column=4, rowspan=2, columnspan=2, padx=2, pady=2
        )  # RIGHT
        x_y_frame.down_y_btn.grid(
            row=4, column=2, rowspan=2, columnspan=2, padx=2, pady=2
        )  # DOWN
        x_y_frame.down_x_btn.grid(
            row=2, column=0, rowspan=2, columnspan=2, padx=2, pady=2
        )  # LEFT
        x_y_frame.increment_box.grid(
            row=3, column=2, rowspan=1, columnspan=2, padx=2, pady=2
        )  # Increment spinbox
        x_y_frame.increment_box.widget.set_precision(-1)

    def get_widget(x_y_frame):
        """Returns the frame widget

        Parameters
        ----------
        x_y_frame : XYFrame
            The XYFrame object

        Returns
        -------
        tk.Frame
            The frame widget
        """

        return x_y_frame.increment_box

    def get_buttons(x_y_frame):
        """Returns the buttons in the frame

        Parameters
        ----------
        x_y_frame : XYFrame
            The XYFrame object

        Returns
        -------
        dict
            A dictionary of the buttons
        """
        names = ["up_x_btn", "down_x_btn", "up_y_btn", "down_y_btn", "zero_xy_btn"]
        return {k: getattr(x_y_frame, k) for k in names}
    
    def toggle_button_states(x_y_frame, joystick_is_on = False, joystick_axes = []):
        """Switches the images used as buttons between two states

        Parameters
        ----------
        x_y_frame : XYFrame
            The XYFrame object
        joystick_is_on : bool
            False if buttons are normal, True if buttons are disabled
        joystick_axes : list
            Contains strings representing joystick axes

        """
        
        for axis in x_y_frame.button_axes_dict.keys():
            if axis in joystick_axes:
                buttons = x_y_frame.button_axes_dict[axis]
                axis_ascii = ord(axis)
                if joystick_is_on:
                    button_state = "disabled"
                    image_list = x_y_frame.disabled_images
                    hover_list = x_y_frame.disabled_hover_texts
                else:
                    button_state = "normal"
                    image_list = x_y_frame.normal_images
                    hover_list = x_y_frame.normal_hover_texts
                for k in range(len(buttons)):
                        buttons[k]['state'] = button_state
                        buttons[k].config(image = image_list[2*(axis_ascii%2)+k])
                        buttons[k].hover.setdescription(hover_list[2*(axis_ascii%2)+k])

class StopFrame(ttk.Frame):
    """Frame for the stop button

    Parameters
    ----------
    stage_control_tab : StageControlTab
        The stage control tab
    name : str
        The name of the frame
    *args
        Variable length argument list
    **kwargs
        Arbitrary keyword arguments

    Attributes
    ----------
    name : str
        The name of the frame
    stop_btn : tk.Button
        The stop button

    Methods
    -------
    get_buttons()
        Returns the buttons in the frame
    """

    def __init__(self, stage_control_tab, name, *args, **kwargs):
        # Init Frame
        ttk.Frame.__init__(self, stage_control_tab, *args, **kwargs)
        self.name = name

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Stop button
        self.stop_btn = tk.Button(
            self, bg="red", fg="white", text="STOP", width=20, height=6
        )

        self.joystick_btn = HoverTkButton(
            self, bg="white", fg="black", text="Enable Joystick", width=15, height=2
        )

        # Gridding out buttons
        self.stop_btn.grid(row=0, column=0, rowspan=2, pady=2)
        self.joystick_btn.grid(row=2, column=0, rowspan=2, pady=2)

    def get_buttons(self):
        return {"stop": self.stop_btn,
                "joystick": self.joystick_btn
                }

    def toggle_button_states(stop_frame, joystick_is_on = False, joystick_axes = []):
        """Switches the images used as buttons between two states

        Parameters
        ----------
        stop_frame : StopFrame
            The StopFrame object
        joystick_is_on : bool
            False if the normal button visuals are in use

        """
        if joystick_is_on:
            stop_frame.joystick_btn.config(text="Disable Joystick")
        else:
            stop_frame.joystick_btn.config(text="Enable Joystick")