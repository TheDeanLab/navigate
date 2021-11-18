from tkinter import *
from tkinter import ttk


class settings_notebook(ttk.Notebook):
    def __init__(setntbk, frame_left, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(setntbk, frame_left, *args, **kwargs)
        #Putting notebook 1 into left frame
        setntbk.grid(row=0,column=0)
        #Creating the settings tab
        setntbk.settings_tab = settings_tab(setntbk)
        #Creating the advanced settings tab
        setntbk.adv_settings_tab = adv_settings_tab(setntbk)
        #Adding tabs to settings notebook
        setntbk.add(setntbk.settings_tab, text='Settings',sticky=NSEW)
        setntbk.add(setntbk.adv_settings_tab, text='Advanced Settings', sticky=NSEW)

class settings_tab(ttk.Frame):
    def __init__(settings, setntbk, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(settings, setntbk, *args, **kwargs)

class adv_settings_tab(ttk.Frame):
    def __init__(adv_settings, setntbk, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(adv_settings, setntbk, *args, **kwargs)
