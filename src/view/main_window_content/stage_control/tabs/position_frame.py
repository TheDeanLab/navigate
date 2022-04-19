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


class position_frame(ttk.Frame):
    def __init__(position_frame, stage_control_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(position_frame, stage_control_tab, *args, **kwargs)

        #Creating each entry frame for a label and entry

        #X Entry
        position_frame.x_val = DoubleVar()
        position_frame.x_entry_frame = ttk.Frame(position_frame)
        position_frame.x_entry = ttk.Entry(position_frame.x_entry_frame, textvariable=position_frame.x_val, width=15)
        position_frame.x_entry_label = ttk.Label(position_frame.x_entry_frame, text="X")
        position_frame.x_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.x_entry.grid(row=0, column=1, sticky="w")

        #Y Entry
        position_frame.y_val = DoubleVar()
        position_frame.y_entry_frame = ttk.Frame(position_frame)
        position_frame.y_entry = ttk.Entry(position_frame.y_entry_frame, textvariable=position_frame.y_val, width=15)
        position_frame.y_entry_label = ttk.Label(position_frame.y_entry_frame, text="Y")
        position_frame.y_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.y_entry.grid(row=0, column=1, sticky="w")

        #Z Entry
        position_frame.z_val = DoubleVar()
        position_frame.z_entry_frame = ttk.Frame(position_frame)
        position_frame.z_entry = ttk.Entry(position_frame.z_entry_frame, textvariable=position_frame.z_val,width=15)
        position_frame.z_entry_label = ttk.Label(position_frame.z_entry_frame, text="Z")
        position_frame.z_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.z_entry.grid(row=0, column=1, sticky="w")

        #Theta Entry
        position_frame.theta_val = DoubleVar()
        position_frame.theta_entry_frame = ttk.Frame(position_frame)
        position_frame.theta_entry = ttk.Entry(position_frame.theta_entry_frame, textvariable=position_frame.theta_val,width=15)
        position_frame.theta_entry_label = ttk.Label(position_frame.theta_entry_frame, text="\N{Greek Capital Theta Symbol}")
        position_frame.theta_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.theta_entry.grid(row=0, column=1, sticky="w")

        #Focus Entry
        position_frame.focus_val = DoubleVar()
        position_frame.focus_entry_frame = ttk.Frame(position_frame)
        position_frame.f_entry = ttk.Entry(position_frame.focus_entry_frame, textvariable=position_frame.focus_val, width=15)
        position_frame.focus_entry_label = ttk.Label(position_frame.focus_entry_frame, text="Focus")
        position_frame.focus_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.f_entry.grid(row=0, column=1, sticky="w")

        '''
        Grid for frames

                1   2   3   4   5

        x is 1
        y is 2
        z is 3
        theta is 4
        focus is 5
        '''

        #Gridding out each frame in postiion frame
        position_frame.x_entry_frame.grid(row=0, column=0, padx=5, sticky=(NSEW))
        position_frame.y_entry_frame.grid(row=0, column=1, padx=5, sticky=(NSEW))
        position_frame.z_entry_frame.grid(row=0, column=2, padx=5, sticky=(NSEW))
        position_frame.theta_entry_frame.grid(row=0, column=3, padx=5, sticky=(NSEW))
        position_frame.focus_entry_frame.grid(row=0, column=4, padx=5, sticky=(NSEW))
