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
from tkinter import ttk, NSEW, Grid
from tkinter.font import Font
# Local Imports
from view.custom_widgets.LabelInputWidgetFactory import LabelInput
from view.custom_widgets.validation import ValidatedSpinbox

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)


class x_y_frame(ttk.Frame):
    def __init__(x_y_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(x_y_frame, stage_control_tab, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(x_y_frame, 'all', weight=1)
        Grid.rowconfigure(x_y_frame, 'all', weight=1)

        #Setting up buttons for up, down, left, right, zero and increment spinbox
        s = ttk.Style()
        s.configure('arrow.TButton', font=(None, 20))


        #Up button
        x_y_frame.up_y_btn = ttk.Button(
            x_y_frame,
            style='arrow.TButton',
            width=10,
            text="\N{UPWARDS BLACK ARROW}"
        )
        #Down button
        x_y_frame.down_y_btn = ttk.Button(
            x_y_frame,
            style='arrow.TButton',
            width=10,
            text="\N{DOWNWARDS BLACK ARROW}"
        )

        #Right button
        x_y_frame.up_x_btn = ttk.Button(
            x_y_frame,
            style='arrow.TButton',
            width=10,
            text="\N{RIGHTWARDS BLACK ARROW}"
        )

        #Left button
        x_y_frame.down_x_btn = ttk.Button(
            x_y_frame,
            style='arrow.TButton',
            width=10,
            text="\N{LEFTWARDS BLACK ARROW}"
        )

        #Zero button
        x_y_frame.zero_xy_btn = ttk.Button(
            x_y_frame,
            text="ZERO XY"
        )

        #Increment spinbox
        x_y_frame.increment_box = LabelInput(
            parent=x_y_frame,
            input_class=ValidatedSpinbox,
            input_var=tk.DoubleVar(),
            input_args={'width': 23}
        )

        #Toggle Method
        def Toggle():
            if x_y_frame.wasd_btn.config('text')[-1] == 'WASD Enabled':
                WASD_movmement(False)
                x_y_frame.wasd_btn.config(text='WASD Disabled')
            else:
                WASD_movmement(True)
                x_y_frame.wasd_btn.config(text='WASD Enabled')
        
        #WASD Movement Method
        def WASD_movmement(temp_bool):
            if (temp_bool):
                 def key_pressed(event):
                     print(f'Key pressed: {event.char}')
                     x_y_frame.bind("<Key>", key_pressed)
            pass

        #WASD Enable/Disable Button
        x_y_frame.wasd_btn = ttk.Button(
            x_y_frame,
            text="WASD Enabled",
            command=Toggle
        )






        '''
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
        '''




        #Gridding out buttons
        x_y_frame.up_y_btn.grid(row=0, column=2, rowspan=2, columnspan=2, padx=2, pady=2) #UP
        x_y_frame.up_x_btn.grid(row=2, column=4, rowspan=2, columnspan=2, padx=2, pady=2) #RIGHT
        x_y_frame.down_y_btn.grid(row=4, column=2, rowspan=2, columnspan=2, padx=2, pady=2) #DOWN
        x_y_frame.down_x_btn.grid(row=2, column=0, rowspan=2, columnspan=2, padx=2, pady=2) #LEFT
        x_y_frame.zero_xy_btn.grid(row=2, column=2, rowspan=1, columnspan=2, padx=2, pady=(5,2), sticky=(NSEW)) #Zero xy
        x_y_frame.increment_box.grid(row=3, column=2, rowspan=1, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #Increment spinbox
        x_y_frame.wasd_btn.grid(row=0, column=1, padx=2, pady=2) #WASD Enable/Disable Button




    def get_widget(x_y_frame):
        return x_y_frame.increment_box

    def get_buttons(x_y_frame):
        names = ['up_x_btn', 'down_x_btn', 'up_y_btn', 'down_y_btn', 'zero_xy_btn', 'wasd_btn']
        return {k: getattr(x_y_frame, k) for k in names}

    def wasd_char(x_y_frame):
        return 
