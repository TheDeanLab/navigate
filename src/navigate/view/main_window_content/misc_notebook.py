# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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
#
# Standard Imports
import tkinter as tk
import logging
from tkinter import ttk
from typing import Iterable, Dict, Any

# Third Party Imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Local Imports
from navigate.view.custom_widgets.DockableNotebook import DockableNotebook

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MiscNotebook(DockableNotebook):
    """Settings Notebook

    This class is the settings notebook. It contains the following tabs:
    - Channels
    - Camera Settings
    - Stage Control
    - Multiposition
    """

    def __init__(
        self,
        bottom_right_frame: ttk.Frame,
        root: tk.Tk,
        *args: Iterable,
        **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the settings notebook

        Parameters
        ----------
        bottom_right_frame : ttk.Frame
            Left frame of the main window
        root : tk.Tk
            Root window of the main window
        *args : list
            Arguments
        **kwargs : dict
            Keyword arguments
        """

        # Init notebook
        DockableNotebook.__init__(self, bottom_right_frame, root, *args, **kwargs)

        # Putting notebook 1 into left frame
        self.grid(row=0, column=0)

        #: ChannelsTab: Channels tab
        self.histogram_tab = HistogramTab(self)

        # Tab list
        tab_list = [
            self.histogram_tab,
        ]
        self.set_tablist(tab_list)

        # Adding tabs to settings notebook
        self.add(self.histogram_tab, text="Histogram", sticky=tk.NSEW)


class HistogramTab(tk.Frame):
    """Channels Tab for the Main Window

    This tab is used to set the channels for the stack acquisition.
    """

    def __init__(
        self, misc_notebook: MiscNotebook, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialization of the Channels Tab

        Parameters
        ----------
        misc_notebook : MiscNotebook
            The notebook that this tab is added to
        *args : Iterable
            Positional arguments for tk.Frame
        **kwargs : Dict[str, Any]
            Keyword arguments for tk.Frame
        """
        # Init Frame
        tk.Frame.__init__(self, misc_notebook, *args, **kwargs)

        #: int: The index of the tab
        self.index = 0

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #: ttk.Frame: The frame for the histogram.
        self.frame = ttk.Frame(self)
        self.frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #: tk.Canvas: The canvas for the histogram.
        self.canvas = tk.Canvas(self.frame, width=512 + 150, height=512 // 6)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #: matplotlib.figure.Figure: The figure for the histogram.
        self.figure = Figure(figsize=(4, 1))

        #: FigureCanvasTkAgg: The canvas for the histogram.
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.figure_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
