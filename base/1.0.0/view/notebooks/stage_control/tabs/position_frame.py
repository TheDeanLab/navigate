# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font


class position_frame(ttk.Frame):
    def __init__(position_frame, stage_control_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(position_frame, stage_control_tab, *args, **kwargs)

        #Creating each entry frame for a label and entry

        #X Entry
        position_frame.x_val = DoubleVar()
        position_frame.x_entry_frame = ttk.Frame(position_frame)
        position_frame.x_entry = ttk.Entry(position_frame.x_entry_frame, textvariable=position_frame.x_val, width=15)
        position_frame.x_entry_label = ttk.Label(position_frame.x_entry_frame, text="X")
        position_frame.x_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.x_entry.grid(row=0, column=1, sticky="w")

        #Y Entry
        position_frame.y_val = DoubleVar()
        position_frame.y_entry_frame = ttk.Frame(position_frame)
        position_frame.y_entry = ttk.Entry(position_frame.y_entry_frame, textvariable=position_frame.y_val, width=15)
        position_frame.y_entry_label = ttk.Label(position_frame.y_entry_frame, text="Y")
        position_frame.y_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.y_entry.grid(row=0, column=1, sticky="w")

        #Z Entry
        position_frame.z_val = DoubleVar()
        position_frame.z_entry_frame = ttk.Frame(position_frame)
        position_frame.z_entry = ttk.Entry(position_frame.z_entry_frame, textvariable=position_frame.z_val,width=15)
        position_frame.z_entry_label = ttk.Label(position_frame.z_entry_frame, text="Z")
        position_frame.z_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.z_entry.grid(row=0, column=1, sticky="w")

        #Theta Entry
        position_frame.theta_val = DoubleVar()
        position_frame.theta_entry_frame = ttk.Frame(position_frame)
        position_frame.theta_entry = ttk.Entry(position_frame.theta_entry_frame, textvariable=position_frame.theta_val,width=15)
        position_frame.theta_entry_label = ttk.Label(position_frame.theta_entry_frame, text="\N{Greek Capital Theta Symbol}")
        position_frame.theta_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.theta_entry.grid(row=0, column=1, sticky="w")

        #Focus Entry
        position_frame.focus_val = DoubleVar()
        position_frame.focus_entry_frame = ttk.Frame(position_frame)
        position_frame.focus_entry = ttk.Entry(position_frame.focus_entry_frame, textvariable=position_frame.focus_val, width=15)
        position_frame.focus_entry_label = ttk.Label(position_frame.focus_entry_frame, text="Focus")
        position_frame.focus_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.focus_entry.grid(row=0, column=1, sticky="w")

        '''
        Grid for frames

                1   2   3   4   5

        x is 1
        y is 2
        z is 3
        theta is 4
        focus is 5
        '''

        #Gridding out each frame in postiion frame
        position_frame.x_entry_frame.grid(row=0, column=0, padx=5, sticky=(NSEW))
        position_frame.y_entry_frame.grid(row=0, column=1, padx=5, sticky=(NSEW))
        position_frame.z_entry_frame.grid(row=0, column=2, padx=5, sticky=(NSEW))
        position_frame.theta_entry_frame.grid(row=0, column=3, padx=5, sticky=(NSEW))
        position_frame.focus_entry_frame.grid(row=0, column=4, padx=5, sticky=(NSEW))
