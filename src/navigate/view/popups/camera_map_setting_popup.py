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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk

# Third Party Imports
from matplotlib.pyplot import subplots
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Local Imports
from navigate.view.custom_widgets.popup import PopUp


class CameraMapSettingPopup(PopUp):
    """Popup to create and visualize camera offset and variance map generation."""

    def __init__(
        self,
        root,
        name="Camera Map Settings",
        size="+320+180",
        top=True,
        transient=True,
        *args,
        **kwargs
    ):
        """Initialize the CameraMapSettingPopup.

        Parameters
        ----------
        root : tk.Tk
            Root window.
        name : str, optional
            Name of the popup, by default "Camera Map Settings".
        size : str, optional
            Size of the popup, by default "+320+180".
        top : bool, optional
            Whether the popup should be on top, by default True.
        transient : bool, optional
            Whether the popup should be transient, by default True.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        super().__init__(root, name, size, top, transient, *args, **kwargs)

        #: dict: Dictionary of input widgets.
        self.inputs = {}

        title = ttk.Label(self.content_frame, text="File: ", padding=(2, 5, 0, 0))
        title.grid(row=0, column=0, sticky=tk.NSEW)

        #: tk.StringVar: File name.
        self.file_name = tk.StringVar()
        self.inputs["file_name"] = tk.Entry(
            self.content_frame, textvariable=self.file_name
        )
        self.inputs["file_name"].grid(
            row=0, column=1, sticky=tk.NSEW, padx=(0, 5), pady=(15, 0)
        )

        #: ttk.Button: Open file button.
        self.open_btn = ttk.Button(self.content_frame, text="Open")
        self.open_btn.grid(row=0, column=2, pady=(0, 10))

        title = ttk.Label(self.content_frame, text="Camera: ", padding=(2, 5, 0, 0))
        #: tk.StringVar: Camera name.
        self.camera = tk.StringVar()
        title.grid(row=0, column=3, sticky=tk.NSEW)
        self.inputs["camera"] = ttk.OptionMenu(self.content_frame, self.camera)
        self.inputs["camera"].grid(
            row=0, column=4, sticky=tk.NSEW, padx=(0, 5), pady=(15, 0)
        )
        #: ttk.Button: Create maps button.
        self.map_btn = ttk.Button(self.content_frame, text="Create maps")
        self.map_btn.grid(row=0, column=5, pady=(0, 10))

        # Plot
        self.fig, self.axs = subplots(1, 2, figsize=(5, 5))
        canvas = FigureCanvasTkAgg(self.fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(
            row=1, column=0, columnspan=6, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5)
        )

    def get_widgets(self):
        """Get the input widgets.

        Returns
        -------
        dict
            Dictionary of input widgets.
        """
        return self.inputs
