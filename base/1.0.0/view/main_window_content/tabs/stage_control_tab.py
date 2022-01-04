# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font

# Local Imports

from view.notebooks.tabs.stage_control.position_frame import position_frame
from view.notebooks.tabs.stage_control.x_y_frame import x_y_frame
from view.notebooks.tabs.stage_control.z_frame import z_frame
from view.notebooks.tabs.stage_control.theta_frame import theta_frame
from view.notebooks.tabs.stage_control.focus_frame import focus_frame
from view.notebooks.tabs.stage_control.goto_frame import goto_frame

class stage_control_tab(ttk.Frame):
    def __init__(stage_control_tab, note3, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(stage_control_tab, note3, *args, **kwargs)

        #Building out stage control elements, frame by frame

        #Position Frame
        stage_control_tab.position_frame = position_frame(stage_control_tab)

        #XY Frame
        stage_control_tab.x_y_frame = x_y_frame(stage_control_tab)

        #Z Frame
        stage_control_tab.z_frame = z_frame(stage_control_tab)

        #Theta Frame
        stage_control_tab.theta_frame = theta_frame(stage_control_tab)

        #Focus Frame
        stage_control_tab.focus_frame = focus_frame(stage_control_tab)

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

        #Gridding out frames
        stage_control_tab.position_frame.grid(row=0, column=0, columnspan=5, sticky=(NSEW))
        stage_control_tab.x_y_frame.grid(row=1, column=0, sticky=(NSEW))
        stage_control_tab.z_frame.grid(row=1, column=1, sticky=(NSEW))
        stage_control_tab.theta_frame.grid(row=1, column=2, sticky=(NSEW))
        stage_control_tab.focus_frame.grid(row=1, column=3, sticky=(NSEW))
        stage_control_tab.goto_frame.grid(row=1, column=4, sticky=(NSEW))
