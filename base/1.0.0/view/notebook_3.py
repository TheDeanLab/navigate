from tkinter import *
from tkinter import ttk

class notebook_3(ttk.Notebook):
    def __init__(note3, frame_bot_right, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(note3, frame_bot_right, *args, **kwargs)
        #Putting notebook 3 into bottom right frame
        note3.pack()
        #Creating Tab 1
        note3.tab_1 = tab_1(note3)
        #Creating Tab 2
        note3.tab_2 = tab_2(note3)
        #Adding tabs to note3 notebook
        note3.add(note3.tab_1, text='Tab 1', sticky=NSEW)
        note3.add(note3.tab_2, text='Tab 2', sticky=NSEW)

class tab_1(ttk.Frame):
    def __init__(tab_1, note3, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(tab_1, note3, *args, **kwargs) 

class tab_2(ttk.Frame):
    def __init__(tab_2, note3, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(tab_2, note3, *args, **kwargs) 