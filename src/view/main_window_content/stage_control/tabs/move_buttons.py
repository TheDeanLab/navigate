import tkinter as tk
from tkinter import ttk

class move_buttons(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):   
        #Init Frame
        ttk.Frame.__init__(self, parent, *args, **kwargs)

        # Setting up frames