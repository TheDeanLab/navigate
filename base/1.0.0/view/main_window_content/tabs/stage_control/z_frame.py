# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font

class z_frame(ttk.Frame):
    def __init__(z_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(z_frame, stage_control_tab, *args, **kwargs)

        #Setting up buttons for up, down, zero and increment spinbox

        #Up button
        z_frame.up_btn = ttk.Button(
            z_frame,
            text="\N{UPWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Down button
        z_frame.down_btn = ttk.Button(
            z_frame,
            text="\N{DOWNWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Zero button
        z_frame.zero_z_btn = ttk.Button(
            z_frame,
            text="ZERO Z"
            #TODO command=function from connector
        )

        #Increment spinbox
        z_frame.spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        z_frame.increment_box = ttk.Spinbox(
            z_frame,
            from_=0,
            to=5000.0,
            textvariable=z_frame.spinval, #this holds the data in the entry
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
        z_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2, sticky=(NSEW)) #UP
        z_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2, sticky=(NSEW)) #DOWN
        z_frame.zero_z_btn.grid(row=2, column=0, pady=2, sticky=(NSEW)) #Zero Z
        z_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox
