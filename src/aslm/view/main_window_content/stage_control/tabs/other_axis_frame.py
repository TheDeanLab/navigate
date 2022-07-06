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
from view.custom_widgets.validation import ValidatedSpinbox

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

class other_axis_frame(ttk.Frame):
    def __init__(other_axis_frame, stage_control_tab, name, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(other_axis_frame, stage_control_tab, *args, **kwargs)
        other_axis_frame.name = name
        
        # Formatting
        Grid.columnconfigure(other_axis_frame, 'all', weight=1)
        Grid.rowconfigure(other_axis_frame, 'all', weight=1)

        #Setting up buttons for up, down, zero and increment spinbox

        #Up button
        other_axis_frame.up_btn = ttk.Button(
            other_axis_frame,
            style='arrow.TButton',
            text="\N{UPWARDS BLACK ARROW}",
        )

        #Down button
        other_axis_frame.down_btn = ttk.Button(
            other_axis_frame,
            style='arrow.TButton',
            text="\N{DOWNWARDS BLACK ARROW}",
        )

        #Zero button
        other_axis_frame.zero_btn = ttk.Button(
            other_axis_frame,
            text="ZERO " + other_axis_frame.name,
        )

        #Increment spinbox

        other_axis_frame.increment_box = LabelInput(
            parent=other_axis_frame,
            input_class=ValidatedSpinbox,
            input_var=DoubleVar(),
            input_args={'width': 25}
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


        #Gridding out buttons
        other_axis_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2) #UP
        other_axis_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2) #DOWN
        other_axis_frame.zero_btn.grid(row=2, column=0, pady=(5,2), sticky=(NSEW)) #Zero Z
        other_axis_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox

    def get_widget(other_axis_frame):
        return other_axis_frame.increment_box

    def get_buttons(other_axis_frame):
        return {
            'up': other_axis_frame.up_btn,
            'down': other_axis_frame.down_btn,
            'zero': other_axis_frame.zero_btn
        }
class min_other_axis_frame(ttk.Frame):
    def __init__(other_axis_frame, minimized_control, name, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(other_axis_frame, minimized_control, *args, **kwargs)
        other_axis_frame.name = name
        
        # Formatting
        Grid.columnconfigure(other_axis_frame, 'all', weight=1)
        Grid.rowconfigure(other_axis_frame, 'all', weight=1)

        #Setting up buttons for up, down, zero and increment spinbox

        #Up button
        other_axis_frame.up_btn = ttk.Button(
            other_axis_frame,
            text="+",
        )

        #Down button
        other_axis_frame.down_btn = ttk.Button(
            other_axis_frame,
            text="-",
        )

        #Zero button
        other_axis_frame.zero_btn = ttk.Button(
            other_axis_frame,
            text="ZERO " + other_axis_frame.name,
        )

        #Increment spinbox

        other_axis_frame.increment_box = LabelInput(
            parent=other_axis_frame,
            input_class=ValidatedSpinbox,
            input_var=DoubleVar(),
            input_args={'width': 25}
        )


        '''
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
        '''


        #Gridding out buttons
        other_axis_frame.down_btn.grid(row=0, column=0, padx=5, sticky=(N)) #DOWN
        other_axis_frame.increment_box.grid(row=0, column=1, padx=5, sticky=(N)) #Increment spinbox
        other_axis_frame.up_btn.grid(row=0, column=2, padx=5, sticky=(N)) #UP
        other_axis_frame.zero_btn.grid(row=0, column=3, padx=5, sticky=(N)) #Zero Z
        

    def get_widget(other_axis_frame):
        return other_axis_frame.increment_box

    def get_buttons(other_axis_frame):
        return {
            'up': other_axis_frame.up_btn,
            'down': other_axis_frame.down_btn,
            'zero': other_axis_frame.zero_btn
        }
