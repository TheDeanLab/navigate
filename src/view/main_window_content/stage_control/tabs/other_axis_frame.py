# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font

class other_axis_frame(ttk.Frame):
    def __init__(other_axis_frame, stage_control_tab, name, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(other_axis_frame, stage_control_tab, *args, **kwargs)
        other_axis_frame.name = name

        #Setting up buttons for up, down, zero and increment spinbox

        #Up button
        other_axis_frame.up_btn = ttk.Button(
            other_axis_frame,
            text="\N{UPWARDS BLACK ARROW}",
            #TODO command=function from connector
        )

        #Down button
        other_axis_frame.down_btn = ttk.Button(
            other_axis_frame,
            text="\N{DOWNWARDS BLACK ARROW}",
            #TODO command=function from connector
        )

        #Zero button
        other_axis_frame.zero_btn = ttk.Button(
            other_axis_frame,
            text="ZERO " + other_axis_frame.name,
            #TODO command=function from connector
        )

        #Increment spinbox
        other_axis_frame.spinval = DoubleVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        other_axis_frame.spinval.set('25')
        other_axis_frame.increment_box = ttk.Spinbox(
            other_axis_frame,
            from_=0,
            to=5000.0,
            textvariable=other_axis_frame.spinval, #this holds the data in the entry
            increment=25,
            width=9,
            #TODO command= function from connector
        )


        '''
        Grid for buttons

                1
                2
                3
                4
                5
                6

        Up is 1,2
        Down is 5,6
        Increment is 3
        Zero is 4
        '''


        #Gridding out buttons
        other_axis_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2, sticky=(NSEW)) #UP
        other_axis_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2, sticky=(NSEW)) #DOWN
        other_axis_frame.zero_btn.grid(row=2, column=0, pady=2, sticky=(NSEW)) #Zero Z
        other_axis_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox
