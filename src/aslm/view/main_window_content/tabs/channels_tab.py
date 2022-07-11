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

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

from aslm.view.main_window_content.tabs.channels.channel_settings import channel_creator
from aslm.view.main_window_content.tabs.channels.stack_acquisition_settings import stack_acq_frame
from aslm.view.main_window_content.tabs.channels.stack_cycling_settings import stack_cycling_frame
from aslm.view.main_window_content.tabs.channels.stack_timepoint_settings import stack_timepoint_frame
from aslm.view.main_window_content.tabs.channels.multipoint_settings import multipoint_frame, multipoint_list


class channels_tab(ttk.Frame):
    def __init__(self, setntbk, *args, **kwargs):
        # Init Frame
        ttk.Frame.__init__(self, setntbk, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(self, 'all', weight=1)
        Grid.rowconfigure(self, 'all', weight=1)

        # Channel Settings
        self.channel_widgets_frame = channel_creator(self)
        self.channel_widgets_frame.grid(row=0, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        # Stack Acquisition Settings
        self.stack_acq_frame = stack_acq_frame(self)
        self.stack_acq_frame.grid(row=1, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        #Stack Cycling Settings
        #self.stack_cycling_frame = stack_cycling_frame(self)
        #self.stack_cycling_frame.grid(row=2, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        # Time Settings
        self.stack_timepoint_frame = stack_timepoint_frame(self)
        self.stack_timepoint_frame.grid(row=3, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        # Multipoint Enable
        self.multipoint_frame = multipoint_frame(self)
        self.multipoint_frame.grid(row=4, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        # Multipoint List
        self.multipoint_list = multipoint_list(self)
        self.multipoint_list.grid(row=5, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)
