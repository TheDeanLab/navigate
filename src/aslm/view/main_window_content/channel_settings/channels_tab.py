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

import tkinter as tk
from tkinter import ttk
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

from aslm.view.main_window_content.channel_settings.channel_settings_frames.channel_settings import (
    channel_creator,
)
from aslm.view.main_window_content.channel_settings.channel_settings_frames.stack_acquisition_settings import (
    stack_acq_frame,
)
from aslm.view.main_window_content.channel_settings.channel_settings_frames.stack_timepoint_settings import (
    stack_timepoint_frame,
)
from aslm.view.main_window_content.multiposition.multipoint_settings import (
    multipoint_frame,
)
from aslm.view.main_window_content.channel_settings.channel_settings_frames.quick_launch import (
    quick_launch,
)
from aslm.view.main_window_content.channel_settings.channel_settings_frames.confocal_projection_settings import (
    conpro_acq_frame,
)


class channels_tab(tk.Frame):
    def __init__(self, setntbk, *args, **kwargs):
        # Init Frame
        tk.Frame.__init__(self, setntbk, *args, **kwargs)

        self.index = 0

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Channel Settings
        self.channel_widgets_frame = channel_creator(self)
        self.channel_widgets_frame.grid(
            row=0, column=0, columnspan=3, sticky=(tk.NSEW), padx=10, pady=10
        )

        # Stack Acquisition Settings
        self.stack_acq_frame = stack_acq_frame(self)
        self.stack_acq_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.NSEW), padx=10, pady=10
        )

        # Time Settings
        self.stack_timepoint_frame = stack_timepoint_frame(self)
        self.stack_timepoint_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.NSEW), padx=10, pady=10
        )

        # Multipoint Enable
        self.multipoint_frame = multipoint_frame(self)
        self.multipoint_frame.grid(
            row=4, column=0, columnspan=1, sticky=(tk.NSEW), padx=10, pady=10
        )

        # Quick Launch Buttons
        self.quick_launch = quick_launch(self)
        self.quick_launch.grid(
            row=4, column=1, columnspan=2, sticky=(tk.NSEW), padx=10, pady=10
        )

        # Confocal Projection Settings
        self.conpro_acq_frame = conpro_acq_frame(self)
        self.conpro_acq_frame.grid(
            row=5, column=0, columnspan=2, sticky=(tk.NSEW), padx=10, pady=10
        )