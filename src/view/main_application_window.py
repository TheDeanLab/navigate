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

A main window is created and passed to the mainapp class. This class will init as a frame then config the main window. It then
creates a menubar using the menubar class. Adds the options for each file menu. It then sets up the frames, then grids the frames.
Finally it uses the notebook classes to put them into the respective frames on the grid. Each of the notebook classes includes tab
classes and inits those etc. The second parameter in each classes __init__ function is the parent. I used the name of the parent
so that it would be easier to keep track of inheritances. Once you have the parent name you can look to the parents class in the
class definition. For example for class Main_App(ttk.Frame) the parent to Main_App is a frame and its name is root. I also used
the name of the class instead of self to make things easier to read. So for Main_App self is now mainapp.
"""

# Import Standard Libraries
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.constants import NSEW
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

# Import Notebooks
from .main_window_content.settings_notebook import settings_notebook
from .main_window_content.camera_notebook import camera_waveform_notebook
from .main_window_content.stagecontrol_notebook import stagecontrol_maxintensity_notebook
from .main_window_content.acquire_bar_frame.acquire_bar import AcquireBar
from .main_window_content.menus import menubar


# Creates the frame that will hold the GUI content, its parent is the main
# window or root Tk object
class Main_App(ttk.Frame):
    # Takes a Tk object should be something like root = Tk() then
    # root_window(root)

    def __init__(mainapp, root, *args, **kwargs):
        # Inits this class as a frame subclass with the root as its parent
        ttk.Frame.__init__(mainapp, root, *args, **kwargs)

        # This starts the main window config, and makes sure that any child
        # widgets can be resized with the window
        mainapp.root = root
        mainapp.root.title("Axially Swept Light-Sheet Microscope")
        # keep icons relative to view directory structure
        view_directory = Path(__file__).resolve().parent
        photo_image = view_directory.joinpath("icon", "mic.png")
        mainapp.root.iconphoto(True, PhotoImage(file=photo_image))
        mainapp.root.resizable(True, True)
        factor = (3/4) # This changes how much of the screen to use. 1 is essentially fullscreen on startup
        screen_width = int(root.winfo_screenwidth() * factor)
        screen_height = int(root.winfo_screenheight() * factor)
        mainapp.root.geometry(f"{screen_width}x{screen_height}")
        Grid.columnconfigure(root, 'all', weight=1)
        Grid.rowconfigure(root, 'all', weight=1)

        # Creating and linking menu to main window/app
        mainapp.menubar = menubar(root)

        # Top Frame Acquire Bar
        mainapp.top_frame = ttk.Frame(mainapp)
        # mainapp.top_frame_label = ttk.Label(mainapp.top_frame, text="Acquire Bar")
        # mainapp.top_frame_label.grid(row=0,column=0)

        # Left Frame Notebook 1 setup
        mainapp.frame_left = ttk.Frame(mainapp)
        # mainapp.left_frame_label = ttk.Label(mainapp.frame_left, text="Notebook #1")
        # mainapp.left_frame_label.grid(row=0,column=0)

        # Top right Frame Notebook 2 setup
        mainapp.frame_top_right = ttk.Frame(mainapp)
        # mainapp.top_right_frame_label = ttk.Label(mainapp.frame_top_right, text="Notebook #2")
        # mainapp.top_right_frame_label.grid(row=0,column=0)

        # Bottom right Frame Notebook 3 setup
        mainapp.frame_bottom_right = ttk.Frame(mainapp)
        # mainapp.bottom_right_frame_label = ttk.Label(mainapp.frame_bottom_right, text="Notebook #3")
        # mainapp.bottom_right_frame_label.grid(row=0,column=0)

        '''
                Placing the notebooks using grid. While the grid is called on each frame it is actually calling
                the main window since those are the parent to the frames. The labels have already been packed into each respective
                frame so can be ignored in the grid setup. This layout uses a 2x2 grid to start.

                        1   2
                        3   4
                        5   6

                The above is the grid "spots" the left frame will take spots 3 & 5 while top right takes
                spot 4 and bottom right frame takes spot 6. Top frame will be spots 1 & 2
                '''

        # Gridding out foundational frames
        mainapp.grid(column=0, row=0, sticky=(NSEW))
        # Sticky tells which walls of gridded cell the widget should stick to,
        # in this case its sticking to the main window on all sides
        mainapp.top_frame.grid(row=0, column=0, columnspan=2, sticky=(NSEW), padx=3, pady=3)
        mainapp.frame_left.grid(row=1, column=0, rowspan=2, sticky=(NSEW), padx=3, pady=3)
        mainapp.frame_top_right.grid(row=1, column=1, sticky=(NSEW), padx=3, pady=3)
        mainapp.frame_bottom_right.grid(row=2, column=1, sticky=(NSEW), padx=3, pady=3)

        # Putting Notebooks into frames, tabs are held within the class of each
        # notebook
        mainapp.settings = settings_notebook(mainapp.frame_left)
        mainapp.camera_waveform = camera_waveform_notebook(mainapp.frame_top_right)
        mainapp.stage_control = stagecontrol_maxintensity_notebook(mainapp.frame_bottom_right)
        mainapp.acqbar = AcquireBar(mainapp.top_frame, mainapp.root)
        logger.info("GUI started")


if __name__ == '__main__':
    root = tk.Tk()
    Main_App(root)
    root.mainloop()
    
