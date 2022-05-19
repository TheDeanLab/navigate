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
from view.custom_widgets.popup import PopUp
from view.custom_widgets.LabelInputWidgetFactory import LabelInput
from view.custom_widgets.validation import ValidatedSpinbox


class remote_popup():
    '''
    #### Class creates the popup that has the ETL parameters.
    '''

    def __init__(self, root, *args, **kwargs):

        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        self.popup = PopUp(
            root,
            "Remote Focus Settings",
            '+320+180',
            top=False,
            transient=False)

        # Storing the content frame of the popup, this will be the parent of
        # the widgets
        content_frame = self.popup.get_frame()
        content_frame.columnconfigure(0, pad=5)
        content_frame.columnconfigure(1, pad=5)
        content_frame.rowconfigure(0, pad=5)
        content_frame.rowconfigure(1, pad=5)
        content_frame.rowconfigure(2, pad=5)
        
        # Formatting
        Grid.columnconfigure(content_frame, 'all', weight=1)
        Grid.rowconfigure(content_frame, 'all', weight=1)

        '''Creating the widgets for the popup'''
        # Dictionary for all the variables
        self.inputs = {}
        self.buttons = {}

        # Frames for widgets
        self.mode_mag_frame = ttk.Frame(content_frame, padding=(0, 5, 0, 0))
        self.save_frame = ttk.Frame(content_frame)
        self.laser_frame = ttk.Frame(content_frame)
        self.high_low_frame = ttk.Frame(content_frame, padding=(0, 5, 0, 0))

        # Gridding Frames
        self.mode_mag_frame.grid(row=0, column=0, sticky=(NSEW))
        self.save_frame.grid(row=0, column=1, sticky=(NSEW))
        self.laser_frame.grid(row=1, column=0, columnspan=2, sticky=(NSEW))
        self.high_low_frame.grid(row=2, column=0, columnspan=2, sticky=(NSEW))

        '''Filling Frames with widgets'''

        # Mode/Mag Frame
        self.inputs["Mode"] = LabelInput(parent=self.mode_mag_frame,
                                         label="Mode",
                                         input_class=ttk.Combobox,
                                         input_var=StringVar(),
                                         label_args={'padding': (2, 5, 48, 0)}
                                         )
        self.inputs["Mode"].grid(row=0, column=0)
        self.inputs["Mode"].state(['readonly'])

        self.inputs["Mag"] = LabelInput(parent=self.mode_mag_frame,
                                        label="Magnification",
                                        input_class=ttk.Combobox,
                                        input_var=StringVar(),
                                        label_args={'padding': (2, 5, 5, 0)}
                                        )
        self.inputs["Mag"].grid(row=1, column=0)
        self.inputs["Mag"].state(['readonly'])

        # Save Frame
        self.buttons['Save'] = ttk.Button(
            self.save_frame, text="Save Configuration")
        self.buttons['Save'].grid(
            row=0, column=0, sticky=(NSEW), padx=(
                5, 0), pady=(
                5, 0))

        # Laser Frame
        title_labels = ['Laser', 'Amplitude', 'Offset']
        laser_labels = ['488nm', '562nm', '642nm']
        # Loop for widgets
        for i in range(3):
            # Title labels
            title = ttk.Label(
                self.laser_frame,
                text=title_labels[i],
                padding=(
                    2,
                    5,
                    0,
                    0))
            title.grid(row=0, column=i, sticky=(NSEW), padx=(0,5))
            # Laser labels
            laser = ttk.Label(
                self.laser_frame,
                text=laser_labels[i],
                padding=(
                    2,
                    5,
                    0,
                    0))
            laser.grid(row=i + 1, column=0, sticky=(NSEW))
            # Entry Widgets
            self.inputs[laser_labels[i] + ' Amp'] = LabelInput(
                parent=self.laser_frame, input_class=ValidatedSpinbox, input_var=StringVar())
            self.inputs[laser_labels[i] + ' Amp'].grid(row=i + 1, column=1, sticky=(NSEW), pady=(20,0), padx=(0,5))
            
            self.inputs[laser_labels[i] + ' Off'] = LabelInput(
                parent=self.laser_frame, input_class=ValidatedSpinbox, input_var=StringVar())
            self.inputs[laser_labels[i] + ' Off'].grid(row=i + 1, column=2, sticky=(NSEW), pady=(20,0))
        
        

        # High/Low Resolution
        hi_lo_labels = ['Percent Delay', 'Duty Cycle', 'Percent Smoothing']
        dict_labels = ['Delay', 'Duty', 'Smoothing']
        # The below code could be in the loop above but I thought it was best
        # to make it separate since they are different frames
        for i in range(3):
            self.inputs[dict_labels[i]] = LabelInput(parent=self.high_low_frame,
                                                     input_class=ttk.Entry,
                                                     label=hi_lo_labels[i],
                                                     input_var=StringVar(),
                                                     label_args={'padding': (2, 5, 5, 0)}
                                                     )
            self.inputs[dict_labels[i]].grid(
                row=i, column=0, sticky=(NSEW), padx=(2, 5))

        # Padding Entry Widgets
        self.inputs['Delay'].pad_input(30, 0, 0, 0)
        self.inputs['Duty'].pad_input(45, 0, 0, 0)
        # self.inputs['Smoothing'].pad_input(0,0,0,0)

    # Getters
    def get_variables(self):
        '''
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        '''
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
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
    remote_popup(root)
    root.mainloop()
