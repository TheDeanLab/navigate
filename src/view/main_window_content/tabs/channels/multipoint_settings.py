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
import tkinter as tk
from tkinter import ttk, Grid
from tkinter.constants import NSEW
import logging
from pathlib import Path

import pandas as pd
from pandastable import Table
from .multi_position_table import Multi_Position_Table as MPTable


class multipoint_frame(ttk.Labelframe):
    def __init__(multipoint_frame, settings_tab, *args, **kwargs):

        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        logger = logging.getLogger(p)

        text_label = 'Multi-position Acquisition'
        ttk.Labelframe.__init__(multipoint_frame, settings_tab, text=text_label, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(multipoint_frame, 'all', weight=1)
        Grid.rowconfigure(multipoint_frame, 'all', weight=1)

        # Save Data Label
        label_position = 0
        input_position = 4
        multipoint_frame.laser_label = ttk.Label(multipoint_frame, text='Enable')
        multipoint_frame.laser_label.grid(row=0, column=label_position, sticky=(NSEW), padx=(4,1), pady=(4,6))

        # Save Data Checkbox
        multipoint_frame.on_off = tk.BooleanVar()
        multipoint_frame.save_check = ttk.Checkbutton(multipoint_frame, text='', variable=multipoint_frame.on_off)
        multipoint_frame.save_check.grid(row=0, column=input_position, sticky=(NSEW), pady=(4,6))

class multipoint_list(ttk.Frame):
    """
    Exploring using a pandastable for embedding an interactive list within a tk Frame.
    https://pandastable.readthedocs.io/en/latest/
    """
    def __init__(multipoint_frame, settings_tab, *args, **kwargs):

        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        logger = logging.getLogger(p)

        #Init Frame
        ttk.Frame.__init__(multipoint_frame, settings_tab, *args, **kwargs)

        df = pd.DataFrame({
            'X': [0],
            'Y': [0],
            'Z': [0],
            'R': [0],
            'F': [0]
        })
        # pt = Table(multipoint_frame, showtoolbar=False)
        multipoint_frame.pt = MPTable(multipoint_frame, showtoolbar=False)
        multipoint_frame.pt.show()
        multipoint_frame.pt.model.df = df

