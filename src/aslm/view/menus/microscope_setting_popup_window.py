# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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
from aslm.tools.common_functions import build_ref_name

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MicroscopeSettingPopupWindow:
    """Popup window with waveform parameters for galvos, remote focusing, etc."""

    def __init__(self, root, microscope_info, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        self.popup = PopUp(
            root, "Microscope Settings", "+320+180", top=False, transient=False
        )

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
        label_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        self.microscopes_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        button_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))

        # Griding Frames
        label_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.microscopes_frame.grid(row=0, column=1, sticky=tk.NSEW)
        button_frame.grid(row=1, column=1, sticky=tk.SE)

        self.labels = ['Microscope Name']
        for microscope_name in microscope_info:
            for k in microscope_info[microscope_name].keys():
                device = " ".join(map(lambda v: v.capitalize(), k.split('_')))
                if device not in self.labels:
                    self.labels.append(device)
        self.labels.append('Setting')

        for i, name in enumerate(self.labels):
            l = ttk.Label(label_frame, text=name, padding=(2, 0, 0, 0))
            if i == 0:
                l.grid(row=i, column=0, padx=(0, 5), pady=(5, 30))
            else:
                l.grid(row=i, column=0, padx=(0, 5), pady=(0, 22))

        self.list_microscope_info(microscope_info)

        # button
        self.buttons["confirm"] = ttk.Button(button_frame, text="Confirm")
        self.buttons["confirm"].grid(
            row=0, column=0, sticky=tk.SE, padx=(5, 0), pady=(0, 5)
        )
        self.buttons["cancel"] = ttk.Button(button_frame, text="Cancel")
        self.buttons["cancel"].grid(
            row=0, column=1, sticky=tk.SE, padx=(5, 0), pady=(0, 5)
        )

    def list_microscope_info(self, microscope_info):
        c = 0
        for microscope_name in microscope_info.keys():
            frame = ttk.Frame(self.microscopes_frame, padding=(0, 0, 0, 0))
            frame.grid(row=0, column=c, sticky=tk.NSEW)
            c += 1
            m_name = ttk.Label(frame, text=microscope_name, padding=(2, 0, 0, 0))
            m_name.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 5), pady=(5, 16))
            for i in range(1, len(self.labels)-1):
                device_ref_name = build_ref_name('_', *self.labels[i].lower().split(' '))
                entry = LabelInput(
                    parent=frame,
                    input_class=ttk.Entry,
                    input_var=tk.StringVar(),
                    label_args={"padding": (0, 0, 5, 20)},
                )
                entry.set(microscope_info[microscope_name].get(device_ref_name, ""))
                entry.widget["state"] = "disabled"
                entry.grid(row=i, column=0, sticky=tk.NSEW, padx=(2, 5), pady=(2, 0))
                self.inputs[f"{microscope_name} {device_ref_name}"] = entry
            # usage
            combo = LabelInput(
                parent=frame,
                input_class=ttk.Combobox,
                input_var=tk.StringVar(),
                label_args={"padding": (0, 0, 5, 20)}
            )
            combo.grid(row=len(self.labels), column=0, sticky=tk.SE, padx=(2, 5), pady=(2, 0))
            self.inputs[f"{microscope_name}"] = combo

    # Getters
    def get_variables(self):
        """
        This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """
        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        """
        return self.inputs

    def get_buttons(self):
        """
        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.
        """
        return self.buttons


if __name__ == "__main__":
    root = tk.Tk()
    MicroscopeSettingPopupWindow(root)
    root.mainloop()
