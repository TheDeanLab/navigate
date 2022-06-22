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
# Standard Library Imports
import logging
import tkinter as tk
from tkinter import *
from tkinter import ttk

# Third Party Imports
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Local Imports
from aslm.view.main_window_content.camera_display.camera_view.tabs.image_metrics import image_metrics
from aslm.view.main_window_content.camera_display.camera_view.tabs.palette import palette

# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

class camera_tab(ttk.Frame):
    def __init__(self, cam_wave, *args, **kwargs):
        #  Init Frame
        ttk.Frame.__init__(self, cam_wave, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(self, 'all', weight=1)
        Grid.rowconfigure(self, 'all', weight=1)

        #  Frame that will hold camera image
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, sticky=NSEW)

        # TODO decide on height, width original was 800x800. 4x binning -> 2048 -> 512
        self.canvas = tk.Canvas(self.cam_image, width=512, height=512)
        self.canvas.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        self.matplotlib_figure = Figure(figsize=[6, 6], tight_layout=True)
        self.matplotlib_canvas = FigureCanvasTkAgg(self.matplotlib_figure, self.canvas)

        #  Frame for camera selection and counts
        self.image_metrics = image_metrics(self)
        self.image_metrics.grid(row=1, column=0, sticky=W, padx=5, pady=5)

        #  Frame for scale settings/pallete color
        self.scale_palette = palette(self)
        self.scale_palette.grid(row=0, column=1, sticky=NSEW, padx=5, pady=5)
