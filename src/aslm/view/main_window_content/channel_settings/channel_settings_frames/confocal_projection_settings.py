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
from tkinter import ttk
import logging
from aslm.view.custom_widgets.hovermixin import HoverButton
from aslm.view.custom_widgets.validation import ValidatedSpinbox, ValidatedCombobox
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.hover import hover


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class conpro_acq_frame(ttk.Labelframe):
    def __init__(self, settings_tab, *args, **kwargs):
        # Init Frame
        text_label = 'Confocal Projecion Settings (' + "\N{GREEK SMALL LETTER MU}" + 'm)'
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)
        
        # Formatting
        tk.Grid.columnconfigure(self, 'all', weight=1)
        tk.Grid.rowconfigure(self, 'all', weight=1)

        # Dictionary for widgets and buttons
        self.inputs = {}

        # Frames for widgets
        self.pos_slice = ttk.Frame(self)
        self.cycling = ttk.Frame(self)

        # Gridding Each Holder Frame
        self.pos_slice.grid(row=0, column=0, sticky=(tk.NSEW))
        self.cycling.grid(row=1, column=0, sticky=(tk.NSEW))
        
        # ScanRange Label, Spinbox
        self.scanrange_label = ttk.Label(self.pos_slice, text='Scan Range')
        self.scanrange_label.grid(row=0, column=0, sticky='S')
        self.inputs['scanrange'] = LabelInput(parent=self.pos_slice,
                                              input_class=ValidatedSpinbox,
                                              input_var=tk.DoubleVar(),
                                              input_args={"from_": 0.0, "increment": 0.5, "width": 6}
                                              )
        self.inputs['scanrange'].grid(row=0, column=1, sticky='N', padx=6)
        self.inputs['scanrange'].label.grid(sticky='N')

         # Plane Number Label, spinbox defaults to 1.
        self.n_plane = ttk.Label(self.pos_slice, text='# planes')
        self.n_plane.grid(row=1, column=0, sticky='S')
        self.inputs['n_plane'] = LabelInput(parent=self.pos_slice,
                                              input_class=ValidatedSpinbox,
                                              input_var=tk.DoubleVar(),
                                              input_args={"from_": 1, "increment": 1, "width": 6}
                                              )
        self.inputs['n_plane'].grid(row=1, column=1, sticky='N', padx=6)
        self.inputs['n_plane'].label.grid(sticky='N')

         # Offset Start Label, spinbox
        self.offset_start = ttk.Label(self.pos_slice, text='Offset Start')
        self.offset_start.grid(row=0, column=2, sticky='S')
        self.inputs['offset_start'] = LabelInput(parent=self.pos_slice,
                                              input_class=ValidatedSpinbox,
                                              input_var=tk.DoubleVar(),
                                              input_args={"from_": 0.0, "increment": 0.1, "width": 6}
                                              )
        self.inputs['offset_start'].grid(row=0, column=3, sticky='N', padx=6)
        self.inputs['offset_start'].label.grid(sticky='N')

         # Offset End Label, spinbox
        self.offset_end = ttk.Label(self.pos_slice, text='Offset End')
        self.offset_end.grid(row=1, column=2, sticky='S')
        self.inputs['offset_end'] = LabelInput(parent=self.pos_slice,
                                              input_class=ValidatedSpinbox,
                                              input_var=tk.DoubleVar(),
                                              input_args={"from_": 0.0, "increment": 0.1, "width": 6}
                                              )
        self.inputs['offset_end'].grid(row=1, column=3, sticky='N', padx=6)
        self.inputs['offset_end'].label.grid(sticky='N')

        # Laser Cycling Settings
        self.inputs['cycling'] = LabelInput(parent=self.cycling,
                                            label='Laser Cycling Settings ',
                                            input_class=ValidatedCombobox,
                                            input_var=tk.StringVar(),
                                            input_args={'width': 8}
                                            )
        self.inputs["cycling"].state(["readonly"])  # Makes it so the user cannot type a choice into combobox
        self.inputs["cycling"].grid(row=2, column=2, sticky='NSEW', padx=6, pady=5)
        

        
    # Getters
    def get_variables(self):
        """
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        """
        # variables = {}
        # for key, widget in self.inputs.items():
        #     variables[key] = widget.get()  # returns value of variable, rather than variable
        #                                    # get_variable() returns the variable, but only for a LabeledInput()
        #variables = {'scanrange': self.scanrange_spinval,
        #            'n_plane': self.exp_plane_spinval,
        #            'offset_start': self.offset_start_spinval,
        #            'offset_end': self.offset_end_spinval}
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """
        # This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        """
        return self.inputs


if __name__ == '__main__':
    root = tk.Tk()
    conpro_acq_frame(root)
    root.mainloop()