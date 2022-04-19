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
from tkinter.font import Font

class other_axis_frame(ttk.Frame):
    def __init__(other_axis_frame, stage_control_tab, name, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(other_axis_frame, stage_control_tab, *args, **kwargs)
        other_axis_frame.name = name

        #Setting up buttons for up, down, zero and increment spinbox

        #Up button
        other_axis_frame.up_btn = ttk.Button(
            other_axis_frame,
            text="\N{UPWARDS BLACK ARROW}",
            #TODO command=function from connector
        )

        #Down button
        other_axis_frame.down_btn = ttk.Button(
            other_axis_frame,
            text="\N{DOWNWARDS BLACK ARROW}",
            #TODO command=function from connector
        )

        #Zero button
        other_axis_frame.zero_btn = ttk.Button(
            other_axis_frame,
            text="ZERO " + other_axis_frame.name,
            #TODO command=function from connector
        )

        #Increment spinbox
        other_axis_frame.spinval = DoubleVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        other_axis_frame.spinval.set('25')
        other_axis_frame.increment_box = ttk.Spinbox(
            other_axis_frame,
            from_=0,
            to=5000.0,
            textvariable=other_axis_frame.spinval, #this holds the data in the entry
            increment=25,
            width=9,
            #TODO command= function from connector
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
        other_axis_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2, sticky=(NSEW)) #UP
        other_axis_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2, sticky=(NSEW)) #DOWN
        other_axis_frame.zero_btn.grid(row=2, column=0, pady=2, sticky=(NSEW)) #Zero Z
        other_axis_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox
