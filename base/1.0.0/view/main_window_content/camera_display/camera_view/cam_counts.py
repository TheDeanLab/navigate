from tkinter import *
from tkinter import ttk
from tkinter.font import Font


#Adds the contents of the camera selection/counts frame
class cam_counts(ttk.Frame):
    def __init__(self, cam_view, *args, **kwargs):
        ttk.Frame.__init__(self, cam_view, *args, **kwargs)