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
import logging
import tkinter as tk
from pathlib import Path
from tkinter import ttk, NSEW, StringVar, Grid
from tkinter.scrolledtext import ScrolledText
from view.custom_widgets.popup import PopUp
from view.custom_widgets.LabelInputWidgetFactory import LabelInput
from view.custom_widgets.validation import ValidatedEntry

#Class that handles the dialog box that has all the user entry stuff when you press the Acquisition button
class Acquire_PopUp():
    '''
    #### Class creates the popup that is generated when the Acquire button is pressed and Save File checkbox is selected.
    '''
    def __init__(self, root, *args, **kwargs):

        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        logger = logging.getLogger(p)

        # Creating popup window with this name and size/placement, PopUp is a Toplevel window
        self.popup = PopUp(root, "File Saving Dialog", '450x450+320+180', transient=True)

        # Storing the content frame of the popup, this will be the parent of the widgets
        content_frame = self.popup.get_frame()
        
        # Formatting
        Grid.columnconfigure(content_frame, 'all', weight=1)
        Grid.rowconfigure(content_frame, 'all', weight=1)

        '''Creating the widgets for the popup'''
        #Dictionary for all the variables
        self.inputs = {}
        self.buttons = {}

        #Label for entries
        self.entries_label = ttk.Label(content_frame, text="Please fill out the fields below")
        self.entries_label.grid(row=0, column=0, columnspan=2, sticky=(NSEW), pady=5)

        # Creating Entry Widgets
        entry_names = ['root_directory', 'user', 'tissue', 'celltype', 'label', 'misc']
        entry_labels = ['Root Directory', 'User', 'Tissue Type', 'Cell Type', 'Label', 'Misc. Info']

        # Loop for each entry and label
        for i in range(len(entry_names)):
            if entry_names[i] == 'misc':
                self.inputs[entry_names[i]] = LabelInput(parent=content_frame,
                                            label=entry_labels[i],
                                            input_class=ScrolledText,
                                            input_args={"wrap": tk.WORD, "width": 40, "height": 10}
                                            )
            else:
                self.inputs[entry_names[i]] = LabelInput(parent=content_frame,
                                            label=entry_labels[i],
                                            input_class=ValidatedEntry,
                                            input_var=StringVar(),
                                            input_args={"required": True}
                                            )
            self.inputs[entry_names[i]].grid(row=i+1, column=0, columnspan=2, sticky=(NSEW), padx=5)
            self.inputs[entry_names[i]].label.grid(padx=(0, 20))

        # Formatting
        self.inputs['user'].widget.grid(padx=(53,0))
        self.inputs['tissue'].widget.grid(padx=(16,0))
        self.inputs['celltype'].widget.grid(padx=(28,0))
        self.inputs['label'].widget.grid(padx=(48,0))
        self.inputs['misc'].widget.grid(padx=(24,0))

        #Done and Cancel Buttons
        self.buttons['Cancel'] = ttk.Button(content_frame, text="Cancel Acquisition")
        self.buttons['Cancel'].grid(row=7, column=0, padx=5, sticky=(NSEW))
        self.buttons['Done'] = ttk.Button(content_frame, text="Acquire Data")
        self.buttons['Done'].grid(row=7, column=1, padx=5, sticky=(NSEW))
        

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
        # This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        '''
        return self.inputs

    def get_buttons(self):
        '''
        # This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.
        '''
        return self.buttons


if __name__ == '__main__':
    root = tk.Tk()
    Acquire_PopUp(root)
    root.mainloop()
        