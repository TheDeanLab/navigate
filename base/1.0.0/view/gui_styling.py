from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter.font import Font

class stagecontrol_maxintensity_styling(ttk.Style):
    
    def __init__(self):
        #Inits the style parent objects attributes
        ttk.Style().__init__(self)

        #Arrow Button Style
        self.configure(
            'Arrow.TButton',
            font=('calibri', 14)
        )

        #Increment spinbox
        self.configure(
            'Increment.TSpinbox',
            arrowsize=15
        )


