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
from tkinter import ttk
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

# Import Sub-Frames
from aslm.view.main_window_content.camera_display.camera_view.camera_view_tab import camera_tab
from aslm.view.main_window_content.tabs.waveform_tab import waveform_tab

class camera_waveform_notebook(ttk.Notebook):
    def __init__(cam_wave, frame_top_right, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(cam_wave, frame_top_right, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(cam_wave, 'all', weight=1)
        Grid.rowconfigure(cam_wave, 'all', weight=1)

        #Putting notebook 2 into top right frame
        cam_wave.grid(row=0, column=0)

        #Creating the camera tab
        cam_wave.camera_tab = camera_tab(cam_wave)

        #Creating the waveform settings tab
        cam_wave.waveform_tab = waveform_tab(cam_wave)

        #Adding tabs to cam_wave notebook
        cam_wave.add(cam_wave.camera_tab, text='Camera View', sticky=NSEW)
        cam_wave.add(cam_wave.waveform_tab, text='Waveform Settings', sticky=NSEW)


