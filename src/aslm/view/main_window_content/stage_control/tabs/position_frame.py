"""
Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
# Standard Imports
from tkinter import *
from tkinter import ttk

# Local Imports
from view.custom_widgets.LabelInputWidgetFactory import LabelInput
from view.custom_widgets.validation import ValidatedEntry

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)


class position_frame(ttk.Frame):
    def __init__(position_frame, stage_control_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(position_frame, stage_control_tab, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(position_frame, 'all', weight=1)
        Grid.rowconfigure(position_frame, 'all', weight=1)

        #Creating each entry frame for a label and entry
        position_frame.inputs = {}
        entry_names = ['x', 'y', 'z', 'theta', 'f']
        entry_labels = ['X', 'Y', 'Z', "\N{Greek Capital Theta Symbol}", 'F']       

        # entries
        for i in range(len(entry_names)):
            position_frame.inputs[entry_names[i]] = LabelInput(parent=position_frame,
                                                            label=entry_labels[i],
                                                            input_class=ValidatedEntry,
                                                            input_var=DoubleVar(),
                                                            input_args={'required': True, 'precision': 0.1}
                                                            )
            position_frame.inputs[entry_names[i]].grid(row=i, column=0, pady=1, padx=15)



       

        '''
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
        '''
    def get_widgets(position_frame):
        return position_frame.inputs

    def get_variables(position_frame):
        variables = {}
        for name in position_frame.inputs:
            variables[name] = position_frame.inputs[name].get_variable()
        return variables
