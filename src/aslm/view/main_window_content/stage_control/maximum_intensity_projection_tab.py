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

# Standard Imports
from tkinter import ttk
import tkinter as tk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class maximum_intensity_projection_tab(ttk.Frame):
    def __init__(self, note3, *args, **kwargs):
        # Init Frame
        ttk.Frame.__init__(self, note3, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Generate MIPs
        def xy_mip():
            pass

        def xz_mip():
            pass

        def yz_mip():
            pass

        # the figure that will contain the plot
        fig = Figure(figsize=(11, 3), tight_layout=True)

        #  Data to just fill void
        t = np.arange(0.0, 2.0, 0.01)
        s1 = np.sin(2 * np.pi * t)
        s2 = np.sin(4 * np.pi * t)

        # adding the subplot
        plot1 = fig.add_subplot(131)
        plot1.plot(t, s1)
        fig.gca().set_axis_off()

        plot2 = fig.add_subplot(132)
        plot2.plot(t, s2)
        fig.gca().set_axis_off()

        plot3 = fig.add_subplot(133)
        plot3.plot(t, s2 * 2)
        fig.gca().set_axis_off()

        # creating the Tkinter canvas
        # containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()

        # placing the canvas on the Tkinter window
        # canvas.get_tk_widget().pack()
        canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)

        self.calculate_button = ttk.Button(self, text="Calculate MIPs")
        self.calculate_button.grid(row=1, column=0, sticky=tk.NSEW)
