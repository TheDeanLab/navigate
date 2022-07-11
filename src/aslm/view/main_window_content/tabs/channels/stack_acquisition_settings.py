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
# import logging
from aslm.view.custom_widgets.validation import ValidatedCombobox, ValidatedSpinbox
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class stack_acq_frame(ttk.Labelframe):
    def __init__(self, settings_tab, *args, **kwargs):
        # Init Frame
        text_label = 'Stack Acquisition Settings (' + "\N{GREEK SMALL LETTER MU}" + 'm)'
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(self, 'all', weight=1)
        Grid.rowconfigure(self, 'all', weight=1)

        # Dictionary for widgets and buttons
        self.inputs = {}
        self.buttons = {}

        # Frames for widgets
        self.pos_slice = ttk.Frame(self)
        self.step_size_frame = ttk.Frame(self)
        self.start_pos_frame = ttk.Frame(self)
        self.end_pos_frame = ttk.Frame(self)
        self.slice_frame = ttk.Frame(self)
        self.cycling = ttk.Frame(self)

        # Gridding Each Holder Frame
        self.pos_slice.grid(row=0, column=0, sticky=(NSEW))
        # self.start_pos_frame.grid(row=0, column=0, sticky=NSEW)
        # self.end_pos_frame.grid(row=0, column=1, sticky=NSEW)
        # self.step_size_frame.grid(row=0, column=2, sticky=NSEW)
        # self.slice_frame.grid(row=0, column=3, sticky=NSEW)
        self.cycling.grid(row=1, column=0, sticky=(NSEW))

        # Start Pos Frame (Vertically oriented)
        start_names = ['start_position', 'start_focus']
        start_labels = ["Pos", "Foc"]

        self.start_label = ttk.Label(self.pos_slice, text='Start')
        self.start_label.grid(row=0, column=0, sticky='S')

        for i in range(len(start_names)):
            self.inputs[start_names[i]] = LabelInput(parent=self.pos_slice,
                                                     label=start_labels[i],
                                                     input_class=ValidatedSpinbox,
                                                     input_var=DoubleVar(),
                                                     input_args={"from_": -50000.0, "increment": 0.5, "width": 14}
                                                     )
            self.inputs[start_names[i]].grid(row=i + 1, column=0, sticky='N')
            self.inputs[start_names[i]].label.grid(sticky='N')
        
        # Start button
        self.buttons['set_start'] = ttk.Button(self.pos_slice, text="Set Start Pos/Foc")
        self.buttons['set_start'].grid(row=3, column=0, sticky='N')

        # End Pos Frame (Vertically Oriented)
        end_names = ['end_position', 'end_focus']
        end_labels = ['Pos', 'Foc']

        self.end_label = ttk.Label(self.pos_slice, text='End')
        self.end_label.grid(row=0, column=1, sticky='S')
        for i in range(len(end_names)):
            self.inputs[end_names[i]] = LabelInput(parent=self.pos_slice,
                                                   label=end_labels[i],
                                                   input_class=ValidatedSpinbox,
                                                   input_var=DoubleVar(),
                                                   input_args={"from_": -50000.0, "increment": 0.5, "width": 14}
                                                   )
            self.inputs[end_names[i]].grid(row=i + 1, column=1, sticky='N')
            self.inputs[end_names[i]].label.grid(sticky='N')
        
            # End Button
        self.buttons['set_end'] = ttk.Button(self.pos_slice, text="Set End Pos/Foc")
        self.buttons['set_end'].grid(row=3, column=1, sticky='N')

        # Step Size Frame (Vertically oriented)
        self.step_size_label = ttk.Label(self.pos_slice, text='Step Size')
        self.step_size_label.grid(row=0, column=2, sticky='S')
        self.inputs['step_size'] = LabelInput(parent=self.pos_slice,
                                              input_class=ValidatedSpinbox,
                                              input_var=DoubleVar(),
                                              input_args={"from_": -50000.0, "increment": 0.5, "width": 14}
                                              )
        self.inputs['step_size'].grid(row=1, column=2, sticky='N')

        # Slice Frame (Vertically oriented)
        self.empty_label = ttk.Label(self.pos_slice, text=' ')
        self.empty_label.grid(row=0, column=3, sticky='N')
        slice_names = ['number_z_steps', 'abs_z_start', 'abs_z_end']
        slice_labels = ['# slices', 'Abs Z Start', 'Abs Z Stop']

        for i in range(len(slice_names)):
            self.inputs[slice_names[i]] = LabelInput(parent=self.pos_slice,
                                                     label=slice_labels[i],
                                                     input_class=ValidatedSpinbox,
                                                     input_var=DoubleVar(),
                                                     input_args={"from_": -50000.0, "increment": 0.5, "width": 14}
                                                     )
            self.inputs[slice_names[i]].label.grid(sticky='N')
            self.inputs[slice_names[i]].widget.configure(state='disabled')
            self.inputs[slice_names[i]].grid(row=i + 1, column=3, sticky='N')

        # Laser Cycling Settings
        self.inputs['cycling'] = LabelInput(parent=self.cycling,
                                                     label='Laser Cycling Settings',
                                                     input_class=ValidatedCombobox,
                                                     input_var=StringVar(),
                                                     input_args={'width': 7}
                                                     )
        self.inputs["cycling"].state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        self.inputs["cycling"].grid(row=0, column=0, sticky=(NSEW), padx=6, pady=5)

    # Getters
    def get_variables(self):
        """
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        """
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

    def get_buttons(self):
        """
        # This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.
        """
        return self.buttons


if __name__ == '__main__':
    root = tk.Tk()
    stack_acq_frame(root)
    root.mainloop()





 # self.start_pos_label = ttk.Label(self.start_pos_frame, text='Pos')
        # self.start_pos_label.grid(row=1, column=0, sticky='N', padx=3, pady=(4, 1))
        # self.start_pos_spinval = DoubleVar()
        # self.start_pos_spinbox = ttk.Spinbox(
        #     self.start_pos_frame,
        #     textvariable=self.start_pos_spinval,
        #     from_=-50000.0,
        #     increment=0.5,
        #     width=14
        # )
        # self.start_pos_spinbox.grid(row=1, column=1, sticky='N', padx=3, pady=(3, 6))

        # self.start_foc_label = ttk.Label(self.start_pos_frame, text='Foc')
        # self.start_foc_label.grid(row=2, column=0, sticky='N', padx=3, pady=(4, 1))
        # self.start_foc_spinval = DoubleVar()
        # self.start_foc_spinbox = ttk.Spinbox(
        #     self.start_pos_frame,
        #     textvariable=self.start_foc_spinval,
        #     from_=-50000.0,
        #     increment=0.5,
        #     width=14
        # )
        # self.start_foc_spinbox.grid(row=2, column=1, sticky='N', padx=3, pady=(3, 6))

        # self.set_start_button = ttk.Button(
        #     self.start_pos_frame,
        #     text="Set Start Pos/Foc"
        # )
        # self.set_start_button.grid(row=3, column=1, sticky='N', padx=3, pady=(3, 6))

        # End Pos Frame (Vertically oriented)
        
       
        # self.end_pos_label = ttk.Label(self.end_pos_frame, text='Pos')
        # self.end_pos_label.grid(row=1, column=0, sticky='N', padx=3, pady=(4, 1))
        # self.end_pos_spinval = DoubleVar()
        # self.end_pos_spinbox = ttk.Spinbox(
        #     self.end_pos_frame,
        #     textvariable=self.end_pos_spinval,
        #     from_=-50000.0,
        #     increment=0.5,
        #     width=14
        # )
        # self.end_pos_spinbox.grid(row=1, column=1, sticky='N', padx=3, pady=(3, 6))

        # self.end_foc_label = ttk.Label(self.end_pos_frame, text='Foc')
        # self.end_foc_label.grid(row=2, column=0, sticky='N', padx=3, pady=(4, 1))
        # self.end_foc_spinval = DoubleVar()
        # self.end_foc_spinbox = ttk.Spinbox(
        #     self.end_pos_frame,
        #     textvariable=self.end_foc_spinval,
        #     from_=-50000.0,
        #     increment=0.5,
        #     width=14
        # )
        # self.end_foc_spinbox.grid(row=2, column=1, sticky='N', padx=3, pady=(3, 6))

        # self.set_end_button = ttk.Button(
        #     self.end_pos_frame,
        #     text="Set End Pos/Foc"
        # )
        # self.set_end_button.grid(row=3, column=1, sticky='N', padx=3, pady=(3, 6))

                # self.step_size_spinval = DoubleVar()
        # self.step_size_spinbox = ttk.Spinbox(
        #     self.step_size_frame,
        #     textvariable=self.step_size_spinval,
        #     from_=-50000.0,
        #     increment=0.5,
        #     width=14
        # )
        # self.step_size_spinbox.grid(row=1, column=0, sticky='N', padx=(4, 3), pady=(3, 6))


        # self.slice_label = ttk.Label(self.slice_frame, text='# slices')
        # self.slice_label.grid(row=1, column=0, sticky='N', padx=3, pady=(4, 1))
        # self.slice_spinval = DoubleVar()
        # self.slice_spinbox = ttk.Spinbox(
        #     self.slice_frame,
        #     textvariable=self.slice_spinval,
        #     increment=0.5,
        #     width=14
        # )
        # self.slice_spinbox.state(['disabled'])
        # self.slice_spinbox.grid(row=1, column=1, sticky='N', padx=3, pady=(3, 6))

        # self.abs_z_start_label = ttk.Label(self.slice_frame, text='Abs Z Start')
        # self.abs_z_start_label.grid(row=2, column=0, sticky='N', padx=3, pady=(4, 1))
        # self.abs_z_start_spinval = DoubleVar()
        # self.abs_z_start_spinbox = ttk.Spinbox(
        #     self.slice_frame,
        #     textvariable=self.abs_z_start_spinval,
        #     increment=0.5,
        #     width=14
        # )
        # self.abs_z_start_spinbox.state(['disabled'])
        # self.abs_z_start_spinbox.grid(row=2, column=1, sticky='N', padx=3, pady=(3, 6))

        # self.abs_z_end_label = ttk.Label(self.slice_frame, text='Abs Z Stop')
        # self.abs_z_end_label.grid(row=3, column=0, sticky='N', padx=3, pady=(4, 1))
        # self.abs_z_end_spinval = DoubleVar()
        # self.abs_z_end_spinbox = ttk.Spinbox(
        #     self.slice_frame,
        #     textvariable=self.abs_z_end_spinval,
        #     increment=0.5,
        #     width=14
        # )
        # self.abs_z_end_spinbox.state(['disabled'])
        # self.abs_z_end_spinbox.grid(row=3, column=1, sticky='N', padx=3, pady=(3, 6))


