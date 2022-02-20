from tkinter import ttk


class waveform_tab(ttk.Frame):
    def __init__(self, cam_wave, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(self, cam_wave, *args, **kwargs)
