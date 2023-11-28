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
from aslm.view.custom_widgets.popup import PopUp
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import logging
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class ScrollFrame(ttk.Frame):
    def __init__(self, parent):

        tk.Frame.__init__(self, parent)
        self.canvas = tk.Canvas(self, borderwidth=1)
        self.frame = tk.Frame(self.canvas)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set, width=200)
        
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="y", expand=False)
        self.canvas.create_window(0, 0, window=self.frame, anchor="nw",
                                  tags="self.frame")
        
        self.frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class AdaptiveOpticsPopup():
    def __init__(self, root, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        self.popup = PopUp(
            root,
            "Adaptive Optics",
            '1100x550+320+180',
            top=False,
            transient=False)

        self.mode_names = [
            "Vert. Tilt",
            "Horz. Tilt",
            "Defocus",
            "Vert. Asm.",
            "Oblq. Asm.",
            "Vert. Coma",
            "Horz. Coma",
            "3rd Spherical",
            "Vert. Tre.",
            "Horz. Tre.",
            "Vert. 5th Asm.",
            "Oblq. 5th Asm.",
            "Vert. 5th Coma",
            "Horz. 5th Coma",
            "5th Spherical",
            "Vert. Tetra.",
            "Oblq. Tetra.",
            "Vert. 7th Tre.",
            "Horz. 7th Tre.",
            "Vert. 7th Asm.",
            "Oblq. 7th Asm.",
            "Vert. 7th Coma",
            "Horz. 7th Coma",
            "7th Spherical",
            "Vert. Penta.",
            "Horz. Penta.",
            "Vert. 9th Tetra.",
            "Oblq. 9th Tetra.",
            "Vert. 9th Tre.",
            "Horz. 9th Tre.",
            "Vert. 9th Asm.",
            "Oblq. 9th Asm."
            ]
            
        self.n_modes = 32 # TODO: Don't hardcode... Get from exp file!

        content_frame = self.popup.get_frame()

        """Creating the widgets for the popup"""
        # Dictionary for all the variables
        self.inputs = {}
        self.modes_armed = {}
        self.mode_labels = {}

        self.ao_notebook = ttk.Notebook(master=content_frame)
        self.ao_notebook.grid(row=0, column=2, rowspan=2)

        self.tab_tw = ttk.Frame(master=self.ao_notebook)
        self.ao_notebook.add(self.tab_tw, text='Tony Wilson')
        self.tab_cnn = ttk.Frame(master=self.ao_notebook)
        self.ao_notebook.add(self.tab_cnn, text='CNN-AO')

        tw_widget_frame = ttk.Frame(master=self.tab_tw)
        tw_widget_frame.grid(row=0, column=1)

        self.inputs['iterations'] = LabelInput(tw_widget_frame, label='Iterations:', label_pos='top', input_args={'width': 15})
        self.inputs['iterations'].grid(row=0, column=1, pady=5)
        self.inputs['steps'] = LabelInput(tw_widget_frame, label='Steps:', label_pos='top', input_args={'width': 15})
        self.inputs['steps'].grid(row=1, column=1, pady=5)
        self.inputs['amplitude'] = LabelInput(tw_widget_frame, label='Amplitude:', label_pos='top', input_args={'width': 15})
        self.inputs['amplitude'].grid(row=2, column=1, pady=5)

        tw_start_from_var = tk.StringVar()
        ttk.Label(tw_widget_frame, text='Start from:').grid(row=3, column=1)
        tw_start_from_combo = ttk.Combobox(tw_widget_frame, textvariable=tw_start_from_var, width=20)
        tw_start_from_combo['values'] = ('flat', 'current')
        tw_start_from_combo.state(['readonly'])
        tw_start_from_combo.grid(row=4, column=1, pady=5)
        tw_start_from_combo.current(0)
        self.inputs['from'] = {'button': tw_start_from_combo, 'variable': tw_start_from_var}

        tw_metric_var = tk.StringVar()
        ttk.Label(tw_widget_frame, text='Image metric:').grid(row=5, column=1)
        tw_metric_combo = ttk.Combobox(tw_widget_frame, textvariable=tw_metric_var, width=20)
        tw_metric_combo['values'] = ('Pixel Max', 'Pixel Average', 'DCT Shannon Entropy')
        tw_metric_combo.state(['readonly'])
        tw_metric_combo.grid(row=6, column=1, pady=5)
        tw_metric_combo.current(0)
        self.inputs['metric'] = {'button': tw_metric_combo, 'variable': tw_metric_var}

        self.tony_wilson_button = ttk.Button(tw_widget_frame, text='RUN', width=15)
        self.tony_wilson_button.grid(row=7, column=1, pady=5)

        control_frame = ttk.Frame(content_frame)
        control_frame.grid(row=0, column=0)

        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0)

        self.set_button = ttk.Button(button_frame, text='Set', width=15)
        self.set_button.grid(row=0, column=0, pady=5)
        self.flat_button = ttk.Button(button_frame, text='Flat', width=15)
        self.flat_button.grid(row=1, column=0, pady=5)
        self.zero_button = ttk.Button(button_frame, text='Zero', width=15)
        self.zero_button.grid(row=2, column=0, pady=5)
        self.clear_button = ttk.Button(button_frame, text='Clear All', width=15)
        self.clear_button.grid(row=3, column=0, pady=5)
        self.save_wcs_button = ttk.Button(button_frame, text='Save WCS File', width=15)
        self.save_wcs_button.grid(row=0, column=1, pady=5)
        self.from_wcs_button = ttk.Button(button_frame, text='From WCS File', width=15)
        self.from_wcs_button.grid(row=1, column=1, pady=5)
        self.select_all_modes = ttk.Button(button_frame, text='Select All', width=15)
        self.select_all_modes.grid(row=2, column=1, pady=5)
        self.deselect_all_modes = ttk.Button(button_frame, text='Deselect All', width=15)
        self.deselect_all_modes.grid(row=3, column=1, pady=5)

        scroll = ScrollFrame(control_frame)
        
        for i in range(self.n_modes):
            mode_name = self.mode_names[i]

            self.mode_labels[mode_name] = ttk.Label(scroll.frame, text=self.mode_names[i])
            self.mode_labels[mode_name].grid(row=i, column=0)

            mode_check_var = tk.BooleanVar()
            mode_check_var.set(False)
            mode_check = ttk.Checkbutton(scroll.frame, variable=mode_check_var)
            mode_check.grid(row=i, column=1)
            self.modes_armed[mode_name] = {'button': mode_check, 'variable': mode_check_var}
            
            self.inputs[mode_name] = LabelInput(scroll.frame, input_args={'width': 10})
            self.inputs[mode_name].set(0.0)
            self.inputs[mode_name].grid(row=i, column=2)

        scroll.grid(row=1, column=0)

        self.plot_frame = ttk.Frame(master=content_frame)
        self.plot_frame.grid(row=0, column=1, rowspan=2)

        self.fig = Figure(figsize=(3,5), dpi=100)
        self.mirror_img = self.fig.add_subplot(211)
        self.coefs_bar = self.fig.add_subplot(212)
        self.fig.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.NSEW), padx=(5,5), pady=(5,5))

        self.fig_tw = Figure(figsize=(4,5), dpi=100)
        self.peaks_plot = self.fig_tw.add_subplot(211)
        self.trace_plot = self.fig_tw.add_subplot(212)
        self.fig_tw.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig_tw, master=self.tab_tw)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.NSEW), padx=(5,5), pady=(5,5))

        camera_var = tk.StringVar()
        self.camera_list = ttk.Combobox(master=self.tab_cnn, textvariable=camera_var)
        self.camera_list['values'] = ('cam_0', 'cam_1')
        self.camera_list.grid(row=0, column=0, padx=10, pady=10)
        self.camera_list.current(0)

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def get_widgets(self):
        return self.inputs
    
    def get_labels(self):
        return self.mode_labels

    def get_modes_armed(self):
        return self.modes_armed

    def set_widgets(self, coefs):
        for i, c in enumerate(coefs):
            self.inputs[self.mode_names[i]].set(c)