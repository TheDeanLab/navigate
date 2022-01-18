from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import numpy as np

class stack_cycling_frame(ttk.Labelframe):
    def __init__(stack_acq, settings_tab, *args, **kwargs):

        #Init Frame
        text_label = 'Laser Cycling Settings'
        ttk.Labelframe.__init__(stack_acq, settings_tab, text=text_label, *args, **kwargs)

        #Laser Cycling Frame (Vertically oriented)
        stack_acq.cycling_frame = ttk.Frame(stack_acq)
        stack_acq.cycling_options = StringVar()
        stack_acq.cycling_pull_down = ttk.Combobox(stack_acq, textvariable=stack_acq.cycling_options)
        stack_acq.cycling_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        stack_acq.cycling_pull_down.grid(row=0, column=1, sticky=(NSEW))

        #Gridding Each Holder Frame
        stack_acq.cycling_frame.grid(row=0, column=0, sticky=(NSEW))

