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
from tkinter import NSEW, ttk


from view.custom_widgets.LabelInputWidgetFactory import LabelInput
from view.custom_widgets.validation import ValidatedEntry
class position_frame(ttk.Labelframe):
    def __init__(self, stage_control_tab, *args, **kwargs):

        #Init Frame
        text_label = 'Current Position'
        ttk.Labelframe.__init__(self, stage_control_tab, text=text_label, *args, **kwargs)
        
        # Widgets
        self.inputs = {}

        # Creation of widgets
        self.labels = ['X', 'Y', 'Z', "\N{Greek Capital Theta Symbol}", 'Focus']
        self.names = ['X', 'Y', 'Z', "Theta", 'Focus']
        
        '''
        Grid for frames

                1   2   3   4   5

        x is 1
        y is 2
        z is 3
        theta is 4
        focus is 5
        '''
        
        for i, label in enumerate(self.labels):
            self.inputs[self.names[i]] = LabelInput(parent=self,
                                                            label=label,
                                                            input_class=ValidatedEntry,
                                                            input_var=tk.DoubleVar()
                                                            )
            self.inputs[self.names[i]].grid(row=0, column=i, padx=5, sticky=(NSEW))
        
        
        
        
        
        

        # #Creating each entry frame for a label and entry

        # #X Entry
        # self.x_val = DoubleVar()
        # self.x_entry_frame = ttk.Frame(self)
        # self.x_entry = ttk.Entry(self.x_entry_frame, textvariable=self.x_val, width=15)
        # self.x_entry_label = ttk.Label(self.x_entry_frame, text="X")
        # self.x_entry_label.grid(row=0, column=0, sticky="e")
        # self.x_entry.grid(row=0, column=1, sticky="w")

        # #Y Entry
        # self.y_val = DoubleVar()
        # self.y_entry_frame = ttk.Frame(self)
        # self.y_entry = ttk.Entry(self.y_entry_frame, textvariable=self.y_val, width=15)
        # self.y_entry_label = ttk.Label(self.y_entry_frame, text="Y")
        # self.y_entry_label.grid(row=0, column=0, sticky="e")
        # self.y_entry.grid(row=0, column=1, sticky="w")

        # #Z Entry
        # self.z_val = DoubleVar()
        # self.z_entry_frame = ttk.Frame(self)
        # self.z_entry = ttk.Entry(self.z_entry_frame, textvariable=self.z_val,width=15)
        # self.z_entry_label = ttk.Label(self.z_entry_frame, text="Z")
        # self.z_entry_label.grid(row=0, column=0, sticky="e")
        # self.z_entry.grid(row=0, column=1, sticky="w")

        # #Theta Entry
        # self.theta_val = DoubleVar()
        # self.theta_entry_frame = ttk.Frame(self)
        # self.theta_entry = ttk.Entry(self.theta_entry_frame, textvariable=self.theta_val,width=15)
        # self.theta_entry_label = ttk.Label(self.theta_entry_frame, text="\N{Greek Capital Theta Symbol}")
        # self.theta_entry_label.grid(row=0, column=0, sticky="e")
        # self.theta_entry.grid(row=0, column=1, sticky="w")

        # #Focus Entry
        # self.focus_val = DoubleVar()
        # self.focus_entry_frame = ttk.Frame(self)
        # self.f_entry = ttk.Entry(self.focus_entry_frame, textvariable=self.focus_val, width=15)
        # self.focus_entry_label = ttk.Label(self.focus_entry_frame, text="Focus")
        # self.focus_entry_label.grid(row=0, column=0, sticky="e")
        # self.f_entry.grid(row=0, column=1, sticky="w")

        

        # #Gridding out each frame in postiion frame
        # self.x_entry_frame.grid(row=0, column=0, padx=5, sticky=(NSEW))
        # self.y_entry_frame.grid(row=0, column=1, padx=5, sticky=(NSEW))
        # self.z_entry_frame.grid(row=0, column=2, padx=5, sticky=(NSEW))
        # self.theta_entry_frame.grid(row=0, column=3, padx=5, sticky=(NSEW))
        # self.focus_entry_frame.grid(row=0, column=4, padx=5, sticky=(NSEW))
        
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
