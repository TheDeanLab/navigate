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
#Adds the contents of the camera selection/counts frame
from tkinter import *
from tkinter import ttk
import tkinter as tk

from view.custom_widgets.LabelInputWidgetFactory import LabelInput


class image_metrics(ttk.Labelframe):
    def __init__(self, cam_view, *args, **kwargs):
        # Init Labelframe
        text_label = 'Image Metrics'
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)
        
        # Dictionary for widgets
        self.inputs = {}

        # Labels and names
        self.labels = ['Frames to Avg', 'Image Max Counts', 'Channel']
        self.names = ['Frames', 'Image', 'Channel']

        # Loop for widgets
        for i in range(len(self.labels)):
            if i == 0:
                self.inputs[self.names[i]] = LabelInput(parent=self,
                                                        label=self.labels[i],
                                                        input_class=ttk.Spinbox,
                                                        input_var=IntVar(),
                                                        input_args={'from_':1, 'to':20, 'increment':1, 'width':9}
                                                        )
                self.inputs[self.names[i]].grid(row=0, column=i, sticky=(NSEW))
            if i > 0:
                self.inputs[self.names[i]] = LabelInput(parent=self,
                                                        label=self.labels[i],
                                                        input_class=ttk.Entry,
                                                        input_var=IntVar(),
                                                        input_args={'width':15}
                                                        )
                self.inputs[self.names[i]].grid(row=0, column=i, sticky=(NSEW))

    def get_variables(self):
        '''
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        '''
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables
    
    def get_widgets(self):
        '''
        # This function returns the dictionary that holds the widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        '''
        return self.inputs

        #Stack Max entry
        # self.stack = DoubleVar()
        # self.stack_frame = ttk.Frame(self)
        # self.stack_entry = ttk.Entry(self.stack_frame, textvariable=self.stack, width=15)
        # self.stack_entry_label = ttk.Label(self.stack_frame, text="Stack Max")
        # self.stack_entry_label.grid(row=0, column=0, sticky="s")
        # self.stack_entry.grid(row=0, column=1, sticky="n")
        # self.stack_frame.grid(row=0, column=1, sticky=NSEW)
