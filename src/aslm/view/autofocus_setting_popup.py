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

from tkinter import *
import tkinter as tk
from tkinter import ttk
from aslm.view.custom_widgets.popup import PopUp
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.validation import ValidatedSpinbox
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)
import numpy as np
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class autofocus_popup():
    '''
    #### Class creates the popup to configure autofocus parameters.
    '''

    def __init__(self, root, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        self.popup = PopUp(
            root,
            "Autofocus Settings",
            '+320+180',
            top=False,
            transient=False)

        # Creating content frame
        content_frame = self.popup.get_frame()   
        

        '''Creating the widgets for the popup'''
        # Dictionary for all the variables
        self.inputs = {}
        self.stage_vars = [BooleanVar(False), BooleanVar(False)]

        # Label Lists
        title_labels = ['Select', 'Ranges', 'Step Size']
        setting_names = ['coarse', 'fine']
        setting_labels = ['Coarse', 'Fine']

        # Column Titles
        for i in range(3):
            # Title labels
            title = ttk.Label(
                content_frame,
                text=title_labels[i],
                padding=(
                    2,
                    5,
                    0,
                    0))
            title.grid(row=0, column=i, sticky=(NSEW))
        

        # Widgets
        for i in range(2):
            # Stage labels
            stage = ttk.Checkbutton(
                content_frame,
                text=setting_labels[i],
                variable=self.stage_vars[i]
                )
            stage.grid(row=i + 1, column=0, sticky=(NSEW), padx=5)
            # Entry Widgets
            self.inputs[setting_names[i] + '_range'] = LabelInput(parent=content_frame,
                                                                  input_class=ValidatedSpinbox,
                                                                  input_var=StringVar()
                                                                  )
            self.inputs[setting_names[i] + '_range'].grid(row=i + 1, column=1, sticky=(NSEW), padx=(0, 5), pady=(15, 0))

            self.inputs[setting_names[i] + '_step_size'] = LabelInput(parent=content_frame,
                                                                      input_class=ValidatedSpinbox,
                                                                      input_var=StringVar()
                                                                      )
            self.inputs[setting_names[i] + '_step_size'].grid(row=i + 1, column=2, sticky=(NSEW), padx=(0, 5), pady=(15, 0))

        # Buttons
        self.autofocus_btn = ttk.Button(content_frame, text='Autofocus')
        self.autofocus_btn.grid(row=4, column=2, pady=(0, 10))

        # Plot
        nums = [[1,2], [3,4], [5,6]]
        nums = np.asarray(nums)
        self.fig = Figure(figsize = (5, 5), dpi = 100)
        self.coarse = self.fig.add_subplot(211)
        self.fine = self.fig.add_subplot(212)
        # self.coarse.plot(nums[:, 0], nums[:, 1], 'bo')
        # self.coarse.clear()
        # self.fine.plot(nums[:, 1], nums[:, 0], 'g*')
        canvas = FigureCanvasTkAgg(self.fig, master=content_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=5, column=0, columnspan=3, sticky=(NSEW), padx=(5,5), pady=(5,5))
        # Adding toolbar
        toolbar = NavigationToolbar2Tk(canvas, content_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=5, column=4)


    def get_widgets(self):
        return self.inputs