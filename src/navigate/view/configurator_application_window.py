# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
import tkinter as tk
from tkinter import ttk
import logging
from pathlib import Path

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]


class ConfigurationAssistant(ttk.Frame):
    def __init__(self, root, *args, **kwargs):
        """Initiates the main application window

        Parameters
        ----------
        root : tk.Tk
            The main window of the application
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """

        #: logging.Logger: The logger for this class
        self.logger = logging.getLogger(p)

        #: tk.Tk: The main window of the application
        self.root = root
        self.root.title("navigate Configuration Assistant")

        view_directory = Path(__file__).resolve().parent
        try:
            photo_image = view_directory.joinpath("icon", "mic.png")
            self.root.iconphoto(True, tk.PhotoImage(file=photo_image))
        except tk.TclError:
            pass

        self.root.resizable(True, True)
        self.root.geometry("512x512")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        #: ttk.Frame: The top frame of the application
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

        #: ttk.Frame: The main frame of the application
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=1, column=0, sticky=tk.NSEW)

        #: ttk.Frame: The top frame of the application
        self.initial_window = TopFrame(self.top_frame, self.root)

        #: ttk.Frame: The main frame of the application
        self.microscope_window = MicroscopeConfiguratorWindow(
            self.main_frame, self.root
        )


class TopFrame(ttk.Frame):
    """Top Frame for Configuration Assistant.

    This class is the initial window for the configurator application.
    It contains the following:
    - Entry for number of configurations
    - Continue button
    - Cancel button
    """

    def __init__(self, main_frame, root, *args, **kwargs):
        """Initialize Acquire Bar.

        Parameters
        ----------
        main_frame : ttk.Frame
            Window to place widgets in.
        root : tk.Tk
            Root window of the application.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """

        #: ttk.Frame: The main frame of the application
        self.main_frame = main_frame
        ttk.Frame.__init__(self, self.main_frame, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Entry for number of configurations
        tk.Label(root, text="Number of Microscopes:").grid(row=0, column=0)

        #: tk.Entry: The entry for the number of configurations to create.
        self.num_configs_entry = tk.Entry(root)
        self.num_configs_entry.grid(row=0, column=1)

        #: tk.Button: The button to continue to the next window.
        self.continue_button = tk.Button(root, text="Continue")
        self.continue_button.grid(row=0, column=2)

        #: tk.Button: The button to cancel the application.
        self.cancel_button = tk.Button(root, text="Cancel")
        self.cancel_button.grid(row=0, column=3)


class MicroscopeConfiguratorWindow(ttk.Frame):
    def __init__(self, main_frame, root, *args, **kwargs):
        """Initialize Acquire Bar.

        Parameters
        ----------
        main_frame : ttk.Frame
            Window to place widgets in.
        root : tk.Tk
            Root window of the application.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        # ttk.Frame.__init__(self, self.main_frame, *args, **kwargs)

        # Entry for number of configurations
        tk.Label(root, text="Microscope Configurator").grid(row=1, column=0)
