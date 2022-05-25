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
"""
# Local Imports
from view.main_window_content.stage_control.tabs.other_axis_frame import other_axis_frame
from view.main_window_content.stage_control.tabs.position_frame import position_frame
from view.main_window_content.stage_control.tabs.x_y_frame import x_y_frame
from view.main_window_content.stage_control.tabs.goto_frame import goto_frame
# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import logging
from pathlib import Path
# Logger Setup
p = Path(__file__).resolve().parts[7]
logger = logging.getLogger(p)


class stage_control_tab(ttk.Frame):
    def __init__(stage_control_tab, note3, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(stage_control_tab, note3, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(stage_control_tab, 'all', weight=1)
        Grid.rowconfigure(stage_control_tab, 'all', weight=1)
        

        #Building out stage control elements, frame by frame

        #Position Frame
        stage_control_tab.position_frame = position_frame(stage_control_tab)

        #XY Frame
        stage_control_tab.xy_frame = x_y_frame(stage_control_tab)

        #Z Frame
        stage_control_tab.z_frame = other_axis_frame(stage_control_tab, 'Z')

        #Theta Frame
        stage_control_tab.theta_frame = other_axis_frame(stage_control_tab, 'Theta')

        #Focus Frame
        stage_control_tab.f_frame = other_axis_frame(stage_control_tab, 'Focus')

        #GoTo Frame
        stage_control_tab.goto_frame = goto_frame(stage_control_tab)
        stage_control_tab.goto_frame_label = ttk.Label(stage_control_tab.goto_frame, text="Goto Frame")
        stage_control_tab.goto_frame_label.pack() #For visual mockup purposes


        '''
        Grid for frames
                1   2   3   4   5
                6   7   8   9   10 

        Position frame is 1-5
        xy is 6
        z is 7
        theta is 8
        focus is 9
        goto is 10
        '''

        # Formatting
        Grid.columnconfigure(stage_control_tab.position_frame, 'all', weight=1)
        Grid.rowconfigure(stage_control_tab.position_frame, 'all', weight=1)
        Grid.columnconfigure(stage_control_tab.xy_frame, 'all', weight=1)
        Grid.rowconfigure(stage_control_tab.xy_frame, 'all', weight=1)
        Grid.columnconfigure(stage_control_tab.z_frame, 'all', weight=1)
        Grid.rowconfigure(stage_control_tab.z_frame, 'all', weight=1)
        Grid.columnconfigure(stage_control_tab.theta_frame, 'all', weight=1)
        Grid.rowconfigure(stage_control_tab.theta_frame, 'all', weight=1)
        Grid.columnconfigure(stage_control_tab.f_frame, 'all', weight=1)
        Grid.rowconfigure(stage_control_tab.f_frame, 'all', weight=1)
        Grid.columnconfigure(stage_control_tab.goto_frame, 'all', weight=1)
        Grid.rowconfigure(stage_control_tab.goto_frame, 'all', weight=1)
        
        #Gridding out frames
        factor = 6
        stage_control_tab.position_frame.grid(row=0, column=0, columnspan=5, sticky=(NSEW), pady=(2,0))
        stage_control_tab.xy_frame.grid(row=1, column=0, sticky=(NSEW), padx=10, pady=10*factor)
        stage_control_tab.z_frame.grid(row=1, column=1, sticky=(NSEW), padx=10, pady=10*factor)
        stage_control_tab.theta_frame.grid(row=1, column=2, sticky=(NSEW), padx=10, pady=10*factor)
        stage_control_tab.f_frame.grid(row=1, column=3, sticky=(NSEW), padx=10, pady=10*factor)
        stage_control_tab.goto_frame.grid(row=1, column=4, sticky=(NSEW), padx=10, pady=10*factor)

    def get_widgets(stage_control_tab):
        """
        # this function will return all the input widgets as a dictionary
        # the reference name in the dictionary is the same as in the widget list file
        """
        temp = {
            **stage_control_tab.position_frame.get_widgets()
        }
        for axis in ['xy', 'z', 'theta', 'f']:
            temp[axis+'_step'] = getattr(stage_control_tab, axis+'_frame').get_widget()
        return temp

    def get_variables(stage_control_tab):
        temp = stage_control_tab.get_widgets()
        return {k: temp[k].get_variable() for k in temp}

    def get_buttons(stage_control_tab):
        """
        # this function returns all the buttons in a dictionary
        # the reference name is the same as in widget list
        """
        result = {
            **stage_control_tab.xy_frame.get_buttons()
        }
        for axis in ['z', 'theta', 'f']:
            temp = getattr(stage_control_tab, axis+'_frame').get_buttons()
            result.update({k+'_'+axis+'_btn': temp[k] for k in temp})
        return result
