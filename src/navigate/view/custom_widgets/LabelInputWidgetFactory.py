# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk
import logging

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.validation import ValidatedCombobox, ValidatedSpinbox
from navigate.view.custom_widgets.hover import (
    HoverButton,
    HoverTkButton,
    HoverRadioButton,
    HoverCheckButton,
)

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class LabelInput(ttk.Frame):
    """Widget class that contains label and input together.

    Acknowledgment: Based on the design from "Python GUI Programming:
    A Complete Reference Guide" by Alan D. Moore and B. M. Harwani.

    For reference on widget arguments, visit: https://tkdocs.com/shipman/

    To use kwargs for parent arguments, update kwargs like this:
    kwargs.update(width=900, height=600)
    Ensure you use super().__init__(parent, **kwargs) to override values correctly.

    User Guide:
    Create instances of LabelInput as children of a LabelFrame for grouped data.
    Access the widget within LabelInput using self.widget for customization.
    Example usage:
    LabelInput(settings, label_pos="top", label="Exposure Time",
               input_class=ttk.Spinbox, input_var=tk.IntVar(),
               input_args={"from_": 0.5, "to": 100, "increment": 0.1},
               label_args={"height": 2, "width": 4})

    """

    def __init__(
        self,
        parent,
        label_pos="left",
        label="",
        input_class=ttk.Entry,
        input_var=None,
        input_args=None,
        label_args=None,
        **kwargs,
    ):
        """Initialize LabelInput widget

        Parameters
        ----------
        parent : tk widget
            The parent widget of the LabelInput widget
        label_pos : str, optional
            The position of the label, by default "left"
        label : str, optional
            The text of the label, by default ""
        input_class : tk widget, optional
            The type of input widget, by default ttk.Entry
        input_var : tk variable, optional
            The variable of the input widget, by default None
        input_args : dict, optional
            The arguments of the input widget, by default None
        label_args : dict, optional
            The arguments of the label widget, by default None
        **kwargs : dict
            The arguments of the parent widget, by default None
        """
        # Calls frame constructor using parent and keyword args
        super().__init__(parent, **kwargs)

        # creating access point to input args for input type constructor (uses
        # these args to create the combobox etc.)
        input_args = input_args or {}

        # same for label args (args to create label etc)
        label_args = label_args or {}

        # same for variable of the input, typically this will be a Tk style var
        # like StringVar which can be accessed by any widget in the app
        #: tk.Variable: The variable of the input widget
        self.variable = input_var
        #: tk.Widget: The widget of the input widget
        self.input_class = input_class

        """ Create widgets based on their type, considering formatting differences."""
        if input_class in (
            ttk.Checkbutton,
            ttk.Button,
            ttk.Radiobutton,
            HoverButton,
            HoverTkButton,
            HoverCheckButton,
            HoverRadioButton,
        ):
            input_args["text"] = label
            input_args["variable"] = input_var
        else:
            #: ttk.Label: The label of the input widget
            self.label = ttk.Label(self, text=label, **label_args)
            self.label.grid(row=0, column=0, sticky=(tk.W + tk.E))
            input_args["textvariable"] = input_var

        """Call the passed widget type constructor with the passed args"""
        #: tk.Widget: The widget of the input widget
        self.widget = input_class(self, **input_args)

        """Specify label position"""
        if label_pos == "top":
            self.widget.grid(row=1, column=0, sticky=(tk.W + tk.E))
            self.columnconfigure(0, weight=1)
        else:
            self.widget.grid(row=0, column=1, sticky=(tk.W + tk.E))
            self.rowconfigure(0, weight=1)

    def get(self, default=None):
        """Returns the value of the input widget

        Creating a generic get function to catch all types of widgets,
        this uses the try except block for instances when tkintervariables fails

        Parameters
        ----------
        default: object, optional
            The default value to return if the get value doesn't work

        Returns
        -------
        value : str
            The value of the input widget

        Examples
        --------
        >>> value = self.get()
        """
        try:
            if self.variable:
                return self.variable.get()  # Catches widgets that don't have text
            elif isinstance(self.widget, tk.Text):
                # This is to account for the different formatting with Text widgets
                return self.widget.get("1.0", tk.END)
            else:
                return (
                    self.widget.get()
                )  # Catches all others like the normal entry widget
        except (TypeError, tk.TclError):
            # Catches times when a numeric entry input has a blank, since this
            # cannot be converted into a numeric value
            if default is not None:
                return default
            return ""

    def get_variable(self):
        """Returns the variable of the input widget

        Returns
        -------
        variable : tk variable
            The variable of the input widget

        Examples
        --------
        >>> variable = self.get_variable()
        """
        return self.variable

    def set(self, value, *args, **kwargs):
        """Sets the value of the input widget

        Parameters
        ----------
        value : str
            The value to set the input widget to

        Examples
        --------
        >>> self.set(value)
        """
        if isinstance(self.variable, tk.BooleanVar):
            # This will cast the value to bool if the variable is a Tk
            # BooleanVar, bc Boolean.Var().set() can only accept bool type
            # values
            self.variable.set(bool(value))
        elif self.variable:
            # No casting needed this will set any of the other var types
            # (String, Int, etc)
            self.variable.set(value, *args, **kwargs)
        elif type(self.widget).__name__.endswith(
            "button"
        ):  # Catches button style widgets
            # The below if statment is needed for button types because it needs
            # to be selected or enabled based on some value
            if value:
                self.widget.select()  # If there is a value select the button
            else:
                self.widget.deselect()  # If there is not deselect it
        # Catches Text type objects so the Multiline Text widget and the Entry
        # widget
        elif isinstance(self.widget, tk.Text):
            self.widget.delete("1.0", tk.END)
            # These lines are used for the specfic formatting of the Text
            # widget, 1 is the line and 0 is the char pos of that line
            self.widget.insert("1.0", value)
        elif isinstance(self.widget, ValidatedCombobox):
            self.widget.current(self.widget["values"].index(value))
        else:
            self.widget.delete(0, tk.END)
            # Basic entry widget formatting, dont need the string as the first
            # arg
            self.widget.insert(0, value)

    def set_values(self, values):
        """Set values of a combobox

        This is a function to set the values of a combobox, it will
        automatically set the values and set the first value as the current

        Values should be a list of strings or numbers that
        you want to be options in the specific widget

        Parameters
        ----------
        values : list
            list of values to be set in the widget

        Examples
        --------
        >>> widget.set_values(['a', 'b', 'c'])
        """
        if self.input_class in (
            ttk.Combobox,
            tk.Listbox,
            ttk.Spinbox,
            ValidatedCombobox,
            ValidatedSpinbox,
        ):
            self.widget["values"] = values
        else:
            print(
                "This widget class does not support list options: "
                + str(self.input_class)
            )
            logger.info(
                f"This widget class does not support list options: {self.input_class}"
            )

    def pad_input(self, left, up, right, down):
        """Pad the input widget

        This is a function to pad the input widget, it will
        automatically set the padding of the widget

        Parameters
        ----------
        left : int
            left padding
        up : int
            up padding
        right : int
            right padding
        down : int
            down padding

        Examples
        --------
        >>> widget.pad_input(10, 10, 10, 10)
        """
        self.widget.grid(padx=(left, right), pady=(up, down))
