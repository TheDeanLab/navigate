# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
import logging
from pathlib import Path

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class RobotControlTab(tk.Frame):
    """RobotControlTab

    RobotControlTab is a tab in the main window that allows the user to
    control the robot.

    Parameters
    ----------
    setntbk : Notebook
        The notebook that contains the tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    Methods
    -------
    None
    """

    def __init__(self, setntbk, *args, **kwargs):
        # Init Frame
        tk.Frame.__init__(self, setntbk, *args, **kwargs)

        self.index = 4

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Robot Initialization Buttons
        self.robot_init = RobotInitialization(self)
        self.robot_init.grid(
            row=0, column=0, columnspan=2, sticky=tk.NSEW, padx=10, pady=10
        )

        # Quick Command Buttons
        self.move_sequence = MoveSequence(self)
        self.move_sequence.grid(
            row=5, column=0, columnspan=2, sticky=tk.NSEW, padx=10, pady=10
        )

        # Pause and Play Buttons
        self.pause_play = PausePlay(self)
        self.pause_play.grid(
            row=0, column=3, columnspan=2, sticky=tk.NSEW, padx=10, pady=10
        )

class RobotInitialization(tk.Frame):
    """RobotInitialization

    RobotInitialization is a frame that contains the widgets for initializing
    robot movement.

    Parameters
    ----------
    settings_tab : tk.Frame
        The frame that contains the settings tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    buttons : dict
        A dictionary of all the buttons that are tied to each widget name.
        The key is the widget name, value is the button associated.

    Methods
    -------
    """
    def __init__(self, settings_tab, *args, **kwargs):
        text_label = 'Robot Initialization'
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Initializing Button
        self.buttons = {
            "import": ttk.Button(self, text="Load Positions from Disk"),
            "connect": ttk.Button(self, text="Connect Robot"),
            "export": ttk.Button(self, text="Save Positions to Disk "),
            "launch": ttk.Button(self,text='Launch Robot Jog Wizard')
        }
        counter = 0
        for key, button in self.buttons.items():
            if counter == 0:
                row, column = 0, 0
            elif counter == 1:
                row, column = 0, 1
            elif counter == 2:
                row, column = 1, 0
            elif counter == 3:
                row, column = 1,1

            button.grid(
                row=row, column=column, sticky=tk.NSEW, padx=(4, 1), pady=(4, 6)
            )
            counter += 1
    
class MoveSequence(tk.Frame):
    """MoveSequence

    MoveSequence is a frame that contains the widgets for initializing
    robot movement.

    Parameters
    ----------
    settings_tab : tk.Frame
        The frame that contains the settings tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    buttons : dict
        A dictionary of all the buttons that are tied to each widget name.
        The key is the widget name, value is the button associated.

    Methods
    -------
    """
    def __init__(self, settings_tab, *args, **kwargs):
        text_label = 'Quick Commands'
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Initializing Button
        self.buttons = {
            "stop": ttk.Button(self, text="STOP"),
            "sample_carousel": ttk.Button(self, text="Sample to carousel"),
            "sample_microscope": ttk.Button(self, text="Sample to microscope"),
            
        }
        counter = 0
        for key, button in self.buttons.items():
            if counter == 0:
                row, column = 0, 0
            elif counter == 1:
                row, column = 0, 1
            elif counter == 2:
                row, column = 0, 2

            button.grid(
                row=row, column=column, sticky=tk.NSEW, padx=(4, 1), pady=(4, 6)
            )
            counter += 1

class PausePlay(tk.Frame):
    """PausePlay

    PausePlay is a frame that contains the widgets for pausing and resuming
    robot actions.

    Parameters
    ----------
    settings_tab : tk.Frame
        The frame that contains the settings tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    buttons : dict
        A dictionary of all the buttons that are tied to each widget name.
        The key is the widget name, value is the button associated.

    Methods
    -------
    """
    def __init__(pauseplay_frame, settings_tab, *args, **kwargs):
        ttk.Labelframe.__init__(pauseplay_frame, settings_tab, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(pauseplay_frame, "all", weight=1)
        tk.Grid.rowconfigure(pauseplay_frame, "all", weight=1)

        #Path to pause and play buttons
        image_directory = Path(__file__).resolve().parent
        pauseplay_frame.pause_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "pause.png")
        ).subsample(32,32)
        pauseplay_frame.play_image = tk.PhotoImage(
            file=image_directory.joinpath("images", "play.png")
        ).subsample(32,32)

        # Pause Button
        pauseplay_frame.pause_btn = tk.Button(
            pauseplay_frame, 
            image=pauseplay_frame.pause_image,
            borderwidth=0,
        )
        # Play Button  
        pauseplay_frame.play_btn = tk.Button(
            pauseplay_frame,
            image=pauseplay_frame.play_image,
            borderwidth=0,
        )

        # Gridding out Buttons
        pauseplay_frame.play_btn.grid(
            row=0, column=0, rowspan=1, columnspan=1, padx=2, pady=2
        )
        pauseplay_frame.pause_btn.grid(
            row=0, column=2, rowspan=1, columnspan=1, padx=2, pady=2
        )
