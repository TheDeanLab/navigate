# ASLM Model Waveforms

# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
import logging
import tkinter as tk
from tkinter import ttk


import numpy as np
from aslm.view.main_window_content.camera_display.camera_settings.camera_settings_frames.camera_mode import camera_mode
from aslm.view.main_window_content.camera_display.camera_settings.camera_settings_frames.framerate_info import framerate_info
from aslm.view.main_window_content.camera_display.camera_settings.camera_settings_frames.camera_roi import camera_roi

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class camera_settings_tab(tk.Frame):
    """
    # This class holds and controls the layout of the major label frames for the camera settings tab in the settings notebook. Any imported classes are children that makeup
    # the content of the major frames. If you need to adjust anything in the frames follow the children.
    """
    def __init__(self, setntbk, *args, **kwargs):
        #Init Frame
        tk.Frame.__init__(self, setntbk, *args, **kwargs)

        self.index = 1
        
        # Formatting
        tk.Grid.columnconfigure(self, 'all', weight=1)
        tk.Grid.rowconfigure(self, 'all', weight=1)

        #Camera Modes Frame
        self.camera_mode = camera_mode(self)
        self.camera_mode.grid(row=0, column=0, sticky=(tk.NSEW), padx=10, pady=10)
        
        #Framerate Label Frame
        self.framerate_info = framerate_info(self)
        self.framerate_info.grid(row=0, column=1, sticky=(tk.NSEW), padx=10, pady=10)

        #Region of Interest Settings
        self.camera_roi = camera_roi(self)
        self.camera_roi.grid(row=1, column=0,columnspan=2, sticky=(tk.NSEW), padx=10, pady=10)


