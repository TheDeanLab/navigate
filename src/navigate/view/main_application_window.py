# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from typing import Iterable, Dict, Any

# Third Party Imports

# Local Imports
from navigate.view.main_window_content.settings_notebook import SettingsNotebook
from navigate.view.main_window_content.display_notebook import CameraNotebook
from navigate.view.main_window_content.acquire_notebook import AcquireBar
from navigate.view.main_window_content.menus import Menubar
from navigate.view.custom_widgets.scrollbars import ScrolledFrame

# Logger Setup
p = __name__.split(".")[1]


class MainApp(ttk.Frame):
    """Creates the frame that will hold the GUI content, its parent is the main window
    or root Tk object

    A main window is created and passed to the mainapp class. This class will init as a
    frame then config the main window. It then creates a menubar using the menubar
    class.

    Adds the options for each file menu. It then sets up the frames, then grids the
    frames.

    Finally, it uses the notebook classes to put them into the respective frames on the
    tk.Grid. Each of the notebook classes includes tab classes and inits those etc.

    The second parameter in each class __init__ function is the parent.

    I used the name of the parent so that it would be easier to keep track of
    inheritances.

    Once you have the parent name you can look to the parents class in the class
    definition.

    For example for class Main_App(ttk.Frame) the parent to Main_App is a frame and its
    name is root. I also used the name of the class instead of self to make things
    easier to read. So for Main_App self is now mainapp.

    Placing the notebooks using tk.Grid. While the grid is called on each frame it
    is actually calling the main window since those are the parent to the frames.
    The labels have already been packed into each respective frame so can be ignored
    in the grid setup. This layout uses a 2x2 grid to start.

    1   2
    3   4
    5   6

    The above is the grid "spots" the left frame will take spots 3 & 5 while top
    right takes spot 4 and bottom right frame takes spot 6. Top frame will be
    spots 1 & 2
    """

    def __init__(self, root: tk.Tk, *args: Iterable, **kwargs: Dict[str, Any]) -> None:
        """Initiates the main application window

        Parameters
        ----------
        root : tk.Tk
            The main window of the application
        *args : iterable
            Variable length argument list
        **kwargs : dict
            Arbitrary keyword arguments
        """

        # Inits this class as a frame subclass with the root as its parent
        #: ScrolledFrame: The scrollable version of the main frame for the application
        self.scroll_frame = ScrolledFrame(root)
        self.scroll_frame.grid(row=0, column=0, sticky=tk.NSEW)

        ttk.Frame.__init__(self, self.scroll_frame.interior, *args, **kwargs)

        #: logging.Logger: The logger for this class
        self.logger = logging.getLogger(p)

        #: tk.Tk: The main window of the application
        self.root = root
        self.root.title("navigate")

        # keep icons relative to view directory structure
        view_directory = Path(__file__).resolve().parent
        try:
            photo_image = view_directory.joinpath("icon", "mic.png")
            self.root.iconphoto(True, tk.PhotoImage(file=photo_image))
        except tk.TclError:
            pass

        self.root.resizable(True, True)
        self.root.geometry("")

        tk.Grid.columnconfigure(root, "all", weight=1)
        tk.Grid.rowconfigure(root, "all", weight=1)

        # Creating and linking menu to main window/app
        #: Menubar: The menu bar for the application
        self.menubar = Menubar(root)

        # Top Frame Acquire Bar
        #: ttk.Frame: The top frame of the application
        self.top_frame = ttk.Frame(self)

        # Left Frame Notebook 1 setup
        #: ttk.Frame: The left frame of the application
        self.left_frame = ttk.Frame(self)

        # Top right Frame Notebook 2 setup
        #: ttk.Frame: The top right frame of the application
        self.right_frame = ttk.Frame(self)

        # Grid out foundational frames
        self.grid(column=0, row=0, sticky=tk.NSEW)
        self.top_frame.grid(
            row=0, column=0, columnspan=2, sticky=tk.NSEW, padx=3, pady=3
        )
        self.left_frame.grid(row=1, column=0, rowspan=2, sticky=tk.NSEW, padx=3, pady=3)
        self.right_frame.grid(row=1, column=1, sticky=tk.NSEW, padx=3, pady=3)

        #: SettingsNotebook: The settings notebook for the application
        self.settings = SettingsNotebook(self.left_frame, self.root)

        #: CameraNotebook: The camera notebook for the application
        self.camera_waveform = CameraNotebook(self.right_frame, self.root)

        #: AcquireBar: The acquire bar for the application
        self.acquire_bar = AcquireBar(self.top_frame, self.root)
