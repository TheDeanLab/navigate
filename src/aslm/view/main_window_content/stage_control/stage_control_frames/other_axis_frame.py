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
import tkinter as tk
from tkinter import ttk

# Local Imports
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.validation import ValidatedSpinbox

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class other_axis_frame(ttk.Labelframe):
    def __init__(other_axis_frame, stage_control_tab, name, *args, **kwargs):
        #Init Frame
        label = name
        ttk.Labelframe.__init__(other_axis_frame, stage_control_tab, text= label + " Movement", *args, **kwargs)
        other_axis_frame.name = name
        
        # Formatting
        tk.Grid.columnconfigure(other_axis_frame, 'all', weight=1)
        tk.Grid.rowconfigure(other_axis_frame, 'all', weight=1)

        image_directory = Path(__file__).resolve().parent
        other_axis_frame.up_image = tk.PhotoImage(file=image_directory.joinpath("images", "greyup.png"))
        other_axis_frame.down_image = tk.PhotoImage(file=image_directory.joinpath("images", "greydown.png"))

        #Setting up buttons for up, down, zero and increment spinbox

        #Up button
        other_axis_frame.up_btn = tk.Button(
            other_axis_frame,
            image=other_axis_frame.up_image,
            borderwidth=0
            # style='arrow.TButton',
            # text="\N{UPWARDS BLACK ARROW}",
        )

        #Down button
        other_axis_frame.down_btn = tk.Button(
            other_axis_frame,
            image=other_axis_frame.down_image,
            borderwidth=0
            # style='arrow.TButton',
            # text="\N{DOWNWARDS BLACK ARROW}",
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
            input_var=tk.DoubleVar(),
            input_args={'width': 5}
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
        other_axis_frame.up_btn.grid(row=0, column=0, pady=2) #UP
        other_axis_frame.down_btn.grid(row=3, column=0, pady=2) #DOWN
        other_axis_frame.zero_btn.grid(row=1, column=0, pady=(5,2)) #Zero Z
        other_axis_frame.increment_box.grid(row=2, column=0, pady=2) #Increment spinbox
        other_axis_frame.increment_box.widget.set_precision(-1)


    def get_widget(other_axis_frame):
        return other_axis_frame.increment_box

    def get_buttons(other_axis_frame):
        return {
            'up': other_axis_frame.up_btn,
            'down': other_axis_frame.down_btn,
            'zero': other_axis_frame.zero_btn
        }
