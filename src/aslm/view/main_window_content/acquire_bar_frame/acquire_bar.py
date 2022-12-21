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

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)



class AcquireBar(ttk.Frame):
    r"""
     Class for the acquisition bar found at the top of the main application window.
     Main function is to change acq setting and then call the acquisition top level window
    """
    def __init__(self,
                 top_frame,
                 root,
                 *args,
                 **kwargs):
        #  Init bar with frame attr
        ttk.Frame.__init__(self, top_frame, *args, **kwargs)
        
        # Formatting
        tk.Grid.columnconfigure(self, 'all', weight=1)
        tk.Grid.rowconfigure(self, 'all', weight=1)

        #  Putting bar into frame
        self.grid(row=0, column=0)

        #  Acquire Button
        self.acquire_btn = ttk.Button(self, text="Acquire")

        #  Read Only Pull down menu: continuous, z-stack, single acquisition, projection.
        self.options = tk.StringVar()
        self.pull_down = ttk.Combobox(self, textvariable=self.options)
        self.pull_down['values'] = ('Continuous Scan', 'Z-Stack', 'Single Acquisition', 'Alignment', 'Projection')
        self.pull_down.current(0)
        self.pull_down.state(["readonly"])

        #  Progress Bar: Current Acquisitions and Overall
        self.progBar_frame = ttk.Frame(self)

        #  This is used to hold and grid the two progress bars.Now when this is
        #  loaded into Acbar the progress bars will follow
        self.CurAcq = ttk.Progressbar(self.progBar_frame,
                                      orient=tk.HORIZONTAL,
                                      length=200,
                                      mode='indeterminate')

        #  Change mode to determinate and set steps for more intuitive usage
        self.OvrAcq = ttk.Progressbar(self.progBar_frame,
                                      orient=tk.HORIZONTAL,
                                      length=200,
                                      mode='determinate')
        self.CurAcq.grid(row=0, column=0)
        self.OvrAcq.grid(row=1, column=0)

        #  Exit Button
        self.exit_btn = ttk.Button(self, text="Exit")

        # Stop Stage Button
        self.stop_stage = ttk.Button(self, text="Stop Stage")

        #  Gridding out Bar
        """
            0   1   2   3
        """
        self.acquire_btn.grid(row=0, column=0, sticky=tk.NSEW, pady=(2,2), padx=(2,2))
        self.pull_down.grid(row=0, column=1, sticky=tk.NSEW, pady=(2,2), padx=(2,2))
        self.progBar_frame.grid(row=0, column=2, sticky=tk.NSEW, pady=(2,2), padx=(2,2))
        self.stop_stage.grid(row=0, column=3, sticky=tk.NSEW, pady=(2,2), padx=(2,2))
        self.exit_btn.grid(row=0, column=4, sticky=tk.NSEW, pady=(2,2), padx=(2,2))
