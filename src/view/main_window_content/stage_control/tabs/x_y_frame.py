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

class x_y_frame(ttk.Frame):
    def print_up():
        print('Up was pressed')
    def __init__(x_y_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(x_y_frame, stage_control_tab, *args, **kwargs)

        #Setting up buttons for up, down, left, right, zero and increment spinbox

        #Up button
        x_y_frame.positive_y_btn = ttk.Button(
            x_y_frame,
            text="\N{UPWARDS BLACK ARROW}"
            #command=
        )

        #Down button
        x_y_frame.negative_y_btn = ttk.Button(
            x_y_frame,
            text="\N{DOWNWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Right button
        x_y_frame.positive_x_btn = ttk.Button(
            x_y_frame,
            text="\N{RIGHTWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Left button
        x_y_frame.negative_x_btn = ttk.Button(
            x_y_frame,
            text="\N{LEFTWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Zero button
        x_y_frame.zero_x_y_btn = ttk.Button(
            x_y_frame,
            text="ZERO XY"
            #TODO command=function from connector
        )

        #Increment spinbox
        x_y_frame.spinval = DoubleVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        x_y_frame.increment_box = ttk.Spinbox(
            x_y_frame,
            from_=0,
            to=5000.0,
            textvariable=x_y_frame.spinval, #this holds the data in the entry
            increment=25,
            width=9
            #TODO command= function from connector
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
        x_y_frame.positive_y_btn.grid(row=0, column=2, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #UP
        x_y_frame.positive_x_btn.grid(row=2, column=4, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #RIGHT
        x_y_frame.negative_y_btn.grid(row=4, column=2, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #DOWN
        x_y_frame.negative_x_btn.grid(row=2, column=0, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #LEFT
        x_y_frame.zero_x_y_btn.grid(row=2, column=2, rowspan=1, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #Zero xy
        x_y_frame.increment_box.grid(row=3, column=2, rowspan=1, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #Increment spinbox
