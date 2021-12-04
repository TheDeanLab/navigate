from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np

class camera_settings_tab(ttk.Frame):
    def __init__(cam_settings, setntbk, session, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(cam_settings, setntbk, *args, **kwargs)