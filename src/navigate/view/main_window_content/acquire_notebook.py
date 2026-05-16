# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

# Standard Library Imports
import logging
import tkinter as tk
from tkinter import ttk
from typing import Iterable, Dict, Any

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.common import configure_grid, themed_grid

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AcquireBar(ttk.Frame):
    """Acquire Bar Class.

    Class for the acquisition bar found at the top of the main application window.
    Main function is to change acq setting and then call the acquisition top-
    level window
    """

    def __init__(
        self,
        top_frame: ttk.Frame,
        root: tk.Tk,
        *args: Iterable,
        **kwargs: Dict[str, Any],
    ) -> None:
        """Initialize Acquire Bar.

        Parameters
        ----------
        top_frame : ttk.Frame
            The frame to place the acquire bar in.
        root : tk.Tk
            Root window of the application.
        *args: Iterable
            Variable length argument list.
        **kwargs: Dict[str, Any]
            Arbitrary keyword arguments.
        """
        #  Init bar with frame attr
        ttk.Frame.__init__(self, top_frame, *args, **kwargs)

        # Formatting
        configure_grid(
            self,
            columns={0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0},
            rows={0: 1},
        )

        # Putting bar into frame
        themed_grid(self, row=0, column=0, sticky=tk.NSEW)

        # Acquire Button
        #: ttk.Button: Button to start acquisition
        self.acquire_btn = ttk.Button(self, text="▶ Acquire", style="Accent.TButton")

        # Read Only Pull down menu: continuous, z-stack, single acquisition, projection.
        #: tk.StringVar: Variable to hold the current option selected
        self.options = tk.StringVar()

        #: ttk.Combobox: Pull down menu to select acquisition type
        self.pull_down = ttk.Combobox(self, textvariable=self.options)

        #  Progress Bar: Current Acquisitions and Overall
        #: ttk.Frame: Frame to hold the progress bars
        self.progBar_frame = ttk.Frame(self)

        #  This is used to hold and grid the two progress bars.Now when this is
        #  loaded into acquisition bar, the progress bars will follow
        #: ttk.Progressbar: Progress bar for current acquisition
        self.CurAcq = ttk.Progressbar(
            self.progBar_frame, orient=tk.HORIZONTAL, length=200, mode="indeterminate"
        )

        #  Change mode to determinate and set steps for more intuitive usage
        #: ttk.Progressbar: Progress bar for overall acquisition
        self.OvrAcq = ttk.Progressbar(
            self.progBar_frame, orient=tk.HORIZONTAL, length=200, mode="determinate"
        )

        #: tk.Label: Label to display the current acquisition progress
        self.total_acquisition_label = tk.Label(
            self, text=f"{0:02}" f":{0:02}" f":{0:02}"
        )

        themed_grid(self.CurAcq, row=0, column=0, sticky=tk.EW)
        themed_grid(self.OvrAcq, row=1, column=0, sticky=tk.EW)
        themed_grid(self.total_acquisition_label, row=0, column=3, sticky=tk.NSEW)
        configure_grid(self.progBar_frame, columns={0: 1}, rows={0: 1, 1: 1})

        #: ttk.Button: Button to exit the application
        self.exit_btn = ttk.Button(self, text="Exit")

        #: ttk.Button: Button to stop the stage
        self.stop_stage = ttk.Button(self, text="Stop Stage")

        themed_grid(
            self.acquire_btn,
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx="space_1",
            pady="space_1",
        )
        themed_grid(
            self.pull_down,
            row=0,
            column=1,
            sticky=tk.NSEW,
            padx="space_1",
            pady="space_1",
        )
        themed_grid(
            self.progBar_frame,
            row=0,
            column=2,
            sticky=tk.NSEW,
            padx=("space_1", "layout_control_gap"),
            pady="space_1",
        )
        themed_grid(
            self.stop_stage,
            row=0,
            column=4,
            sticky=tk.NSEW,
            padx="space_1",
            pady="space_1",
        )
        themed_grid(
            self.exit_btn,
            row=0,
            column=5,
            sticky=tk.NSEW,
            padx="space_1",
            pady="space_1",
        )
