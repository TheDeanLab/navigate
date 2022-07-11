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
from view.main_window_content.stage_control.tabs.other_axis_frame import min_other_axis_frame as other_axis_frame
from view.main_window_content.stage_control.tabs.position_frame import min_position_frame as position_frame
from view.main_window_content.stage_control.tabs.x_y_frame import min_x_y_frame as x_y_frame
from view.main_window_content.stage_control.tabs.goto_frame import goto_frame
# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)


class minimized_control(ttk.Frame):
    """
    Stage GUI Control Tab resized and reformatted to fit onto a smaller windowsize. All widgets and variables linked to main stage GUI control
    """
    def __init__(minimized_control, note3, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(minimized_control, note3, *args, **kwargs)
        minimized_control.note3=note3
        
        # Formatting
        Grid.columnconfigure(minimized_control, 'all', weight=1)
        Grid.rowconfigure(minimized_control, 'all', weight=1)
        

        #Building out stage control elements, frame by frame

        #Position Frame
        minimized_control.position_frame = position_frame(minimized_control)
        
        #XY Frame
        minimized_control.xy_frame = x_y_frame(minimized_control)

        #Z Frame
        minimized_control.z_frame = other_axis_frame(minimized_control, 'Z')
        minimized_control.z_frame.increment_box.set(minimized_control.note3.stage_control_tab.z_frame.increment_box.get_variable())

        #Theta Frame
        minimized_control.theta_frame = other_axis_frame(minimized_control, 'Theta')
        minimized_control.theta_frame.increment_box.set(minimized_control.note3.stage_control_tab.theta_frame.increment_box.get_variable().get())

        #Focus Frame
        minimized_control.f_frame = other_axis_frame(minimized_control, 'Focus')
        minimized_control.f_frame.increment_box.set(minimized_control.note3.stage_control_tab.f_frame.increment_box.get())

        #try changing w/ if loop inside of other_axis_frame.py

        #GoTo Frame
        minimized_control.goto_frame = goto_frame(minimized_control)
        minimized_control.goto_frame_label = ttk.Label(minimized_control.goto_frame, text="Goto Frame")
        minimized_control.goto_frame_label.pack() #For visual mockup purposes


        '''
        Grid for frames
                1   2   
                3   4   
                5   6   
                7   8   
                9   10 

        Position frame is 1, 3, 5 , 7, 9
        x is 2
        y is 4
        z is 6
        theta is 8
        focus is 10
        '''

        # Formatting
        Grid.columnconfigure(minimized_control.position_frame, 'all', weight=1)
        Grid.rowconfigure(minimized_control.position_frame, 'all', weight=1)
        Grid.columnconfigure(minimized_control.xy_frame, 'all', weight=1)
        Grid.rowconfigure(minimized_control.xy_frame, 'all', weight=1)
        Grid.columnconfigure(minimized_control.z_frame, 'all', weight=1)
        Grid.rowconfigure(minimized_control.z_frame, 'all', weight=1)
        Grid.columnconfigure(minimized_control.theta_frame, 'all', weight=1)
        Grid.rowconfigure(minimized_control.theta_frame, 'all', weight=1)
        Grid.columnconfigure(minimized_control.f_frame, 'all', weight=1)
        Grid.rowconfigure(minimized_control.f_frame, 'all', weight=1)
        
        # Did not include GOTO widget in remaking of GUI
        Grid.columnconfigure(minimized_control.goto_frame, 'all', weight=1)
        Grid.rowconfigure(minimized_control.goto_frame, 'all', weight=1)
        
        #Gridding out frames
        minimized_control.position_frame.grid(row=0, column=0, rowspan=5, sticky=(NSEW), pady=2)
        minimized_control.xy_frame.grid(row=0, column=1, sticky=(NSEW), padx=5)
        minimized_control.z_frame.grid(row=2, column=1, sticky=(NSEW), padx=5)
        minimized_control.theta_frame.grid(row=3, column=1, sticky=(NSEW), padx=5)
        minimized_control.f_frame.grid(row=4, column=1, sticky=(NSEW), padx=5)
        
    def get_widgets(minimized_control):
        """ Return all the input widgets as a dictionary
        
        Returns
        -------
        temp : dictionary
            Dictionary of each widget with reference value same as in the widget list
        """
        temp = {
            **minimized_control.position_frame.get_widgets()
        }
        for axis in ['xy', 'z', 'theta', 'f']:
            temp[axis+'_step'] = getattr(minimized_control, axis+'_frame').get_widget()
        return temp

    def get_variables(minimized_control):
        temp = minimized_control.get_widgets()
        return {k: temp[k].get_variable() for k in temp}

    def get_buttons(minimized_control):
        """ Return all the buttons as a dictionary
        
        Returns
        -------
        result : dictionary
            Dictionary of each button with reference value same as in the button list
        """
        result = {
            **minimized_control.xy_frame.get_buttons()
        }
        for axis in ['z', 'theta', 'f']:
            temp = getattr(minimized_control, axis+'_frame').get_buttons()
            result.update({k+'_'+axis+'_btn': temp[k] for k in temp})
        return result
