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
            '375x345+320+180',
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

        self.setting_frame = ttk.Frame(content_frame)
        self.setting_frame.grid(row=1, column=0, columnspan=2, sticky=(NSEW))

        '''Creating the widgets for the popup'''
        # Dictionary for all the variables
        self.inputs = {}
        self.stage_vars = [BooleanVar(False), BooleanVar(False)]

        # self.inputs['channel_selector'] = LabelInput(parent=content_frame,
        #                                  label="Channel",
        #                                  input_class=ttk.Combobox,
        #                                  input_var=StringVar(),
        #                                  label_args={'padding': (20, 5, 48, 0)}
        #                                  )
        # self.inputs["channel_selector"].grid(row=0, column=0)
        # self.inputs["channel_selector"].state(['readonly'])

        # Setting Frame
        title_labels = ['Select', 'Ranges', 'Step Size']
        setting_labels = ['stage1', 'stage2']
        # Loop for widgets
        for i in range(3):
            # Title labels
            title = ttk.Label(
                self.setting_frame,
                text=title_labels[i],
                padding=(
                    2,
                    5,
                    0,
                    0))
            title.grid(row=0, column=i, sticky=(NSEW))

        for i in range(2):
            # Stage labels
            stage = ttk.Checkbutton(
                self.setting_frame,
                text=setting_labels[i],
                variable=self.stage_vars[i]
                )
            stage.grid(row=i + 1, column=0, sticky=(NSEW), padx=1, pady=5)
            # Entry Widgets
            self.inputs[setting_labels[i] + '_range'] = LabelInput(
                parent=self.setting_frame, input_class=ValidatedSpinbox, input_var=StringVar())
            self.inputs[setting_labels[i] +
                        '_range'].grid(row=i + 1, column=1, sticky=(NSEW))
            self.inputs[setting_labels[i] + '_step_size'] = LabelInput(
                parent=self.setting_frame, input_class=ValidatedSpinbox, input_var=StringVar())
            self.inputs[setting_labels[i] +
                        '_step_size'].grid(row=i + 1, column=2, sticky=(NSEW))

        self.autofocus_btn = ttk.Button(self.setting_frame, text='Autofocus')
        self.autofocus_btn.grid(row=4, column=2)

    def get_widgets(self):
        return self.inputs