from tkinter import *
from tkinter import ttk
from tkinter.font import Font


class pallete(ttk.Frame):
    def __init__(self, cam_view, *args, **kwargs):
        ttk.Frame.__init__(self, cam_view, *args, **kwargs)

        #Setting up radio box
        self.pallete = ttk.Labelframe(self, text='Pallete Color')
        self.pallete.grid(row=0, column=0, sticky=(NSEW))

        #Radiobuttons for pallete
        self.color = StringVar()
        self.gray = ttk.Radiobutton(self.pallete, text="Gray", variable=self.color, value=0)
        self.gradient = ttk.Radiobutton(self.pallete, text="Gradient", variable=self.color, value=1)
        self.rainbow = ttk.Radiobutton(self.pallete, text="Rainbow", variable=self.color, value=2)
        self.gray.grid(row=0, column=0, sticky=(NSEW))
        self.gradient.grid(row=1, column=0, sticky=(NSEW))
        self.rainbow.grid(row=2, column=0, sticky=(NSEW))

        #Autoscale checkbox
        self.autoscale = BooleanVar()
        self.autoscale_check = ttk.Checkbutton(self, text="Autoscale Z", variable=self.autoscale)
        self.autoscale_check.grid(row=1, column=0, sticky=(NSEW))

        #Scale to counts
        self.count_scale = BooleanVar()
        self.count_check = ttk.Checkbutton(self, text="Scale to Counts", variable=self.count_scale)
        self.count_check.grid(row=2, column=0, sticky=(NSEW))
