"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

A main window is created and passed to the mainapp class. This class will init as a frame then config the main window. It then
creates a menubar using the menubar class. Adds the options for each file menu. It then sets up the frames, then grids the frames.
Finally it uses the notebook classes to put them into the respective frames on the tk.Grid. Each of the notebook classes includes tab
classes and inits those etc. The second parameter in each classes __init__ function is the parent. I used the name of the parent
so that it would be easier to keep track of inheritances. Once you have the parent name you can look to the parents class in the
class definition. For example for class Main_App(ttk.Frame) the parent to Main_App is a frame and its name is root. I also used
the name of the class instead of self to make things easier to read. So for Main_App self is now mainapp.
"""

# Import Standard Libraries
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
import sys

# Third Party Imports

# Local Imports
from aslm.view.main_window_content.settings_notebook import settings_notebook
from aslm.view.main_window_content.camera_display.camera_view.camera_notebook import (
    CameraNotebook,
)
from aslm.view.main_window_content.stage_control.stagecontrol_notebook import (
    stagecontrol_notebook,
)
from aslm.view.main_window_content.acquire_bar_frame.acquire_bar import AcquireBar
from aslm.view.menus.menus import menubar
from aslm.view.custom_widgets.scrollbars import ScrolledFrame


# Logger Setup
p = __name__.split(".")[1]


class MainApp(ttk.Frame):
    r"""Creates the frame that will hold the GUI content, its parent is the main window or root Tk object
    ``
        Placing the notebooks using tk.Grid. While the grid is called on each frame it is actually calling
        the main window since those are the parent to the frames. The labels have already been packed into each respective
        frame so can be ignored in the grid setup. This layout uses a 2x2 grid to start.

        1   2
        3   4
        5   6

        The above is the grid "spots" the left frame will take spots 3 & 5 while top right takes
        spot 4 and bottom right frame takes spot 6. Top frame will be spots 1 & 2
    """

    def __init__(self, root, *args, **kwargs):

        # Inits this class as a frame subclass with the root as its parent
        self.scroll_frame = ScrolledFrame(root)
        self.scroll_frame.grid(row=0, column=0, sticky=tk.NSEW)

        ttk.Frame.__init__(self, self.scroll_frame.interior, *args, **kwargs)

        # Initialize Logger
        self.logger = logging.getLogger(p)

        # This starts the main window config, and makes sure that any child
        # widgets can be resized with the window
        self.root = root
        self.root.title("Axially Swept Light-Sheet Microscope")

        # keep icons relative to view directory structure
        view_directory = Path(__file__).resolve().parent
        photo_image = view_directory.joinpath("icon", "mic.png")
        self.root.iconphoto(True, tk.PhotoImage(file=photo_image))
        self.root.resizable(True, True)
        self.root.geometry("")
        tk.Grid.columnconfigure(root, "all", weight=1)
        tk.Grid.rowconfigure(root, "all", weight=1)

        # Creating and linking menu to main window/app
        self.menubar = menubar(root)

        # Top Frame Acquire Bar
        self.top_frame = ttk.Frame(self)

        # Left Frame Notebook 1 setup
        self.frame_left = ttk.Frame(self)

        # Top right Frame Notebook 2 setup
        self.frame_top_right = ttk.Frame(self)

        # Bottom right Frame Notebook 3 setup
        self.frame_bottom_right = ttk.Frame(self)

        # Gridding out foundational frames
        self.grid(column=0, row=0, sticky=tk.NSEW)
        self.top_frame.grid(
            row=0, column=0, columnspan=2, sticky=tk.NSEW, padx=3, pady=3
        )
        self.frame_left.grid(row=1, column=0, rowspan=2, sticky=tk.NSEW, padx=3, pady=3)
        self.frame_top_right.grid(row=1, column=1, sticky=tk.NSEW, padx=3, pady=3)
        self.frame_bottom_right.grid(row=2, column=1, sticky=tk.NSEW, padx=3, pady=3)

        # Putting Notebooks into frames, tabs are held within the class of each
        # notebook
        self.settings = settings_notebook(self.frame_left, self.root)
        self.camera_waveform = CameraNotebook(self.frame_top_right, self.root)
        # self.stage_control = stagecontrol_notebook(self.frame_bottom_right)

        self.acqbar = AcquireBar(self.top_frame, self.root)
        self.logger.info("GUI setup working")
        self.logger.info("Performance - GUI Started real quick")
        self.logger.info("Spec - GUI is this size")

        # TODO: We do not understand the GUI sizing.  Notes here. Follow-up later when this becomes a problem.
        # Adjust Canvas Width for Screen Resolution
        # Appears that Windows has 96 DPI, and Apple has 72.
        # iMac Built in Retina Display is 4480 x 2520
        # In the settings, can adjust display scaling -> 2560 x 1440
        # dpi = int(self.root.winfo_fpixels('1i'))
        # tk_screen_width, tk_screen_height = int(root.winfo_screenwidth()), int(root.winfo_screenheight()) # 1920 x 1080
        # TK screen width is the correct width according to the OS.

        # Tk doesn't take into account the DPI?
        # actual_screen_width, actual_screen_height = int(tk_screen_width * (dpi / 96)), int(tk_screen_height * (dpi / 96))
        # Take into account the fact that we actually do not have 96 DPI, but actually 72. 2560 x 1440.

        # print(f"TK Screen Width, Height, dpi: {tk_screen_width}, {tk_screen_height}, {dpi}")  # 1920 x 1080
        # print(f"Actual Screen Width, Height: {actual_screen_width}, {actual_screen_height}")  # 2560 x 1440.

        # Is the GUI bigger than the actual or tk screen size?

        # if canvas_width > screen_width or canvas_height > screen_height:
        #     screen_scaling_factor = dpi / 72
        #
        #     self.root.tk.call('tk', 'scaling', screen_scaling_factor)

        # self.root.geometry(f"{actual_screen_width}x{actual_screen_height}")


if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
