# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font

class goto_frame(ttk.Frame):
    def __init__(goto_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(goto_frame, stage_control_tab, *args, **kwargs)
