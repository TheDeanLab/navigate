# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font

class focus_frame(ttk.Frame):
    def __init__(focus_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(focus_frame, stage_control_tab, *args, **kwargs)

        #Setting up focus buttons

        #Up button
        focus_frame.up_btn = ttk.Button(
            focus_frame,
            text="\N{UPWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Down button
        focus_frame.down_btn = ttk.Button(
            focus_frame,
            text="\N{DOWNWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Zero button
        focus_frame.zero_focus_btn = ttk.Button(
            focus_frame,
            text="ZERO Focus"
            #TODO command=function from connector
        )

        #Increment spinbox
        focus_frame.spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        focus_frame.increment_box = ttk.Spinbox(
            focus_frame,
            from_=0,
            to=5000.0,
            textvariable=focus_frame.spinval, #this holds the data in the entry
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
        focus_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2, sticky=(NSEW)) #UP
        focus_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2, sticky=(NSEW)) #DOWN
        focus_frame.zero_focus_btn.grid(row=2, column=0, pady=2, sticky=(NSEW)) #Zero focus
        focus_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox
